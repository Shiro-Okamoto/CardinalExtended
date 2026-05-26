from __future__ import annotations


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .account import Account

    from requests import Response
    from typing import Generator


import logging
from bs4 import BeautifulSoup
from time import time, sleep


from . import (
    exceptions, OrderStatuses, generate_random_tag, BuyerViewing, ChatShortcut, OrderShortcut, InitialChatEvent, ChatsListChangedEvent, LastChatMessageChangedEvent,
    NewMessageEvent, InitialOrderEvent, OrdersListChangedEvent, NewOrderEvent, OrderStatusChangedEvent, RunnerPayload, RunnerObject, RunnerRequest, RunnerResponse,
    INVISIBLE_CHARACTER
)


logger = logging.getLogger("FunPayAPI.runner")


class Runner:
    def __init__(self, account: Account, disable_message_requests: bool = False, disable_order_requests: bool = False):
        '''
        Класс, описывающий метод `/runner` FunPay.

        Получает и сортирует новые события, хранит полезную нагрузку, списки заказов/чатов/сообщений.

        :param account: Экземпляр аккаунта (должен быть инициализирован с помощью метода :meth:`account.Account.get`).
        :type account: :class:`Account`
        :param disable_message_requests: Отключить ли запросы для получения истории чатов, defaults to :obj:`False`.\n
            Если True, :meth:`listen` не будет возвращать события
            * :class:`NewMessageEvent`.\n
            Из событий, связанных с чатами, будут возвращаться только:\n
            * :class:`InitialChatEvent`\n
            * :class:`ChatsListChangedEvent`\n
            * :class:`LastChatMessageChangedEvent`\n
        :type disable_message_requests: :obj:`bool`, опционально
        :param disable_order_requests: Отключить ли запросы для получения списка заказов, defaults to :obj:`False`.\n
            Если True, :meth:`listen` не будет возвращать события
            * :class:`InitialOrderEvent`,
            * :class:`NewOrderEvent`,
            * :class:`OrderStatusChangedEvent`.\n
            Из событий, связанных с заказами, будет возвращаться только
            * :class:`OrdersListChangedEvent`.
        :type disable_order_requests: :obj:`bool`, опционально
        '''
        if not account.is_initiated: raise exceptions.AccountNotInitiatedError()

        if account.runner: exceptions.BoundAccountRunnerError()


        self.account: Account = account
        'Экземпляр аккаунта, к которому привязан Runner.'
        self.account.runner = self


        self.message_requests: bool = False if disable_message_requests else True
        'Делать ли доп. запросы для получения всех новых сообщений изменившихся чатов.'
        self.order_requests: bool = False if disable_order_requests else True
        'Делать ли доп. запросы для получения новых / изменившихся заказов.'


        self.__first_request = True
        'Это первый запрос?'

        self.__last_msg_event_tag = generate_random_tag()
        'Тег последнего события получения истории чатов.'
        self.__last_order_event_tag = generate_random_tag()
        'Тег последнего события получения истории заказов.'

        self.runner_len: int = 10
        'Количество событий, на которое успешно отвечает `/runner`.'


        # -------------------------------- Кеш событий ------------------------------- #
        self.saved_orders: dict[str, OrderShortcut] = {}
        'Сохраненные состояния заказов в виде {айди заказа: :class:`OrderShortcut`}.'

        self.chats_last_messages: dict[int, dict[str, int|str|None]] = {}
        'Список последних сообщений чатов.'

        self.by_bot_ids: dict[int, list[int]] = {}
        'Айди сообщений, отправленных с помощью account.send_message в виде {айди чата: [айди сообщений]}.'

        self.last_message_ids: dict[int, int] = {}
        'Айди последних сообщений в чатах (для событий сообщений при :obj:`message_requests` = True).'

        self.buyers_viewing: dict[int, BuyerViewing] = {}
        '{айди покупателя: :class:`BuyerViewing`}.'


    def send_request(self, payload: RunnerPayload) -> Response:
        '''
        Отправляет запрос runner/ с указанной полезной нагрузкой.

        :param payload: Полезная нагрузка.
        :type payload: :class:`RunnerPayload`
        :return: Объект ответа.
        :rtype: :class:`Response`
        '''
        logger.debug(f'Отправляю запрос: {payload}')

        headers = {
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "x-requested-with": "XMLHttpRequest"
        }

        payload_obj = payload.to_json()
        payload_obj['csrf_token'] = self.account.csrf_token

        return self.account.method('post', 'https://funpay.com/runner/', headers=headers, payload=payload_obj, raise_not_200=True)


    def get_updates(self) -> dict:
        """
        Запрашивает список событий FunPay.

        :return: Ответ запроса.
        :rtype: :obj:`dict`
        """
        orders = RunnerObject(
            'orders_counters',
            self.account.id,
            self.__last_order_event_tag
        )

        chats = RunnerObject(
            'chat_bookmarks',
            self.account.id,
            self.__last_msg_event_tag
        )

        payload = RunnerPayload(
            [orders, chats]
        )

        response = self.send_request(payload)

        json_response = response.json()

        response_obj = RunnerResponse.from_json(json_response)

        logger.debug(f"Получены данные о событиях: {response_obj}")

        return json_response


    def parse_updates(self, updates: dict) -> list[
        InitialChatEvent |
        ChatsListChangedEvent |
        LastChatMessageChangedEvent |
        NewMessageEvent |
        InitialOrderEvent |
        OrdersListChangedEvent |
        NewOrderEvent |
        OrderStatusChangedEvent
    ]:
        """
        Парсит ответ FunPay и создает события.

        :param updates: Результат выполнения :meth:`get_updates`
        :type updates: :obj:`dict`
        :return: Список событий.
        :rtype: :obj:`list[InitialChatEvent | ChatsListChangedEvent | LastChatMessageChangedEvent | NewMessageEvent | InitialOrderEvent | OrdersListChangedEvent |
        NewOrderEvent | OrderStatusChangedEvent]`
        """
        events = []
        # сортируем в т.ч. для того, корректно реагировало на сообщения покупателей сразу после оплаты (плагины автовыдачи)
        for obj in sorted(updates["objects"], key=lambda x: x.get("type") == "orders_counters", reverse=True):
            if obj.get("type") == "chat_bookmarks":
                events.extend(self.parse_chat_updates(obj))
            elif obj.get("type") == "orders_counters":
                events.extend(self.parse_order_updates(obj))
        if self.__first_request:
            self.__first_request = False
        return events


    def parse_chat_updates(self, obj) -> list[InitialChatEvent | ChatsListChangedEvent | LastChatMessageChangedEvent | NewMessageEvent]:
        """
        Парсит события, связанные с чатами.

        :param obj: словарь из результата выполнения :meth:`get_updates`, где "type" == "chat_bookmarks".
        :type obj: :obj:`dict`
        :return: список событий, связанных с чатами.
        :rtype: :obj:`list[InitialChatEvent | ChatsListChangedEvent | LastChatMessageChangedEvent | NewMessageEvent]`
        """
        events, lcmc_events = [], []
        self.__last_msg_event_tag = obj.get("tag")
        parser = BeautifulSoup(obj["data"]["html"], "lxml")
        chats = parser.find_all("a", {"class": "contact-item"})

        # Получаем все изменившиеся чаты
        for chat in chats:
            chat_id = int(chat["data-id"])
            # Если чат удален админами - скип.
            if not (last_msg_text := chat.find("div", {"class": "contact-item-message"})):
                continue

            last_msg_text = last_msg_text.text

            node_msg_id = int(chat.get('data-node-msg'))
            user_msg_id = int(chat.get('data-user-msg'))
            by_bot = False
            if last_msg_text.startswith(INVISIBLE_CHARACTER):
                last_msg_text = last_msg_text[1:]
                by_bot = True
            if self.chats_last_messages.get(chat_id):
                prev_node_msg_id = self.chats_last_messages[chat_id]['node_msg_id']
                prev_user_msg_id = self.chats_last_messages[chat_id]['user_msg_id']
                prev_text = self.chats_last_messages[chat_id]['last_msg_text']
            else: prev_node_msg_id, prev_user_msg_id, prev_text = (-1, -1, None)

            last_msg_text_or_none = None if last_msg_text in ("Изображение", "Зображення", "Image") else last_msg_text
            if node_msg_id <= prev_node_msg_id:
                continue
            elif not prev_node_msg_id and not prev_user_msg_id and prev_text == last_msg_text_or_none:
                # значит сообщение отправлено ботом и оставлено непрочитанным - просто обновляем инфу
                self.chats_last_messages[chat_id] = {
                    'node_msg_id': node_msg_id,
                    'user_msg_id': user_msg_id,
                    'last_msg_text': last_msg_text_or_none
                }
                continue
            unread = True if "unread" in chat.get("class") else False

            chat_with = chat.find("div", {"class": "media-user-name"}).text
            chat_obj = ChatShortcut(chat_id, chat_with, last_msg_text, node_msg_id, user_msg_id, unread, str(chat), by_bot if last_msg_text_or_none is not None else None)

            self.account.add_chats([chat_obj])
            self.chats_last_messages[chat_id] = {
                'node_msg_id': node_msg_id,
                'user_msg_id': user_msg_id,
                'last_msg_text': last_msg_text_or_none
            }
            if self.__first_request:
                events.append(InitialChatEvent(self.__last_msg_event_tag, chat_obj))


                if self.message_requests: self.last_message_ids[chat_id] = node_msg_id


                continue

            else: lcmc_events.append(LastChatMessageChangedEvent(self.__last_msg_event_tag, chat_obj))

        # Если есть события изменения чатов, значит это не первый запрос и ChatsListChangedEvent будет первым событием
        if lcmc_events:
            events.append(ChatsListChangedEvent(self.__last_msg_event_tag))

        if not self.message_requests:
            events.extend(lcmc_events)
            return events

        lcmc_events_without_new_mess = []
        lcmc_events_with_new_mess = []
        for lcmc_event in lcmc_events:
            if lcmc_event.chat.node_msg_id <= self.last_message_ids.get(lcmc_event.chat.id, -1):
                lcmc_events_without_new_mess.append(lcmc_event)
            else:
                lcmc_events_with_new_mess.append(lcmc_event)
        events.extend(lcmc_events_without_new_mess)

        while lcmc_events_with_new_mess:
            chats_pack = lcmc_events_with_new_mess[:self.runner_len]
            del lcmc_events_with_new_mess[:self.runner_len]

            chats_data = {i.chat.id: i.chat.name for i in chats_pack}
            new_msg_events = self.generate_new_message_events(chats_data)

            # [LastChatMessageChanged, NewMSG, NewMSG ..., LastChatMessageChanged, NewMSG, NewMSG ...]
            for i in chats_pack:
                events.append(i)
                if new_msg_events.get(i.chat.id):
                    events.extend(new_msg_events[i.chat.id])
        return events

    def generate_new_message_events(self, chats_data: dict[int, str]) -> dict[int, list[NewMessageEvent]]:
        """
        Получает историю переданных чатов и генерирует события новых сообщений.


        :param chats_data: Айди чатов и никнеймы собеседников (:obj:`None`, если никнейм неизвестен)
        :type chats_data: :obj:`dict`
        :return: Словарь с событиями новых сообщений в формате {айди чата: [список событий]}
        :rtype: :obj:`dict[int, list[NewMessageEvent]]`
        """
        attempts = 3
        while attempts:
            attempts -= 1
            try:
                chats = self.account.get_chats_histories(chats_data)
                break
            except exceptions.RequestFailedError as e:
                logger.error(e)
            except:
                logger.error(f"Не удалось получить истории чатов {list(chats_data.keys())}.")
                logger.debug("TRACEBACK", exc_info=True)
            sleep(1)
        else:
            logger.error(f"Не удалось получить истории чатов {list(chats_data.keys())}: превышено кол-во попыток.")
            return {}

        result = {}

        for cid in chats:
            messages = chats[cid]
            result[cid] = []
            self.by_bot_ids[cid] = self.by_bot_ids.get(cid) or []

            # Удаляем все сообщения, у которых ID меньше сохраненного последнего сообщения
            if self.last_message_ids.get(cid):
                messages = [i for i in messages if i.id > self.last_message_ids[cid]]
            if not messages:
                continue

            # Отмечаем все сообщения, отправленные с помощью Account.send_message()
            if self.by_bot_ids.get(cid):
                for i in messages:
                    if not i.by_bot and i.id in self.by_bot_ids[cid]:
                        i.by_bot = True

            # Если нет сохраненного ID последнего сообщения
            if not self.last_message_ids.get(cid):
                messages = [m for m in messages if
                            m.id > min(self.last_message_ids.values(), default=10 ** 20)] or messages[-1:]

            self.last_message_ids[cid] = messages[-1].id  # Перезаписываем ID последнего сообщение
            self.by_bot_ids[cid] = [i for i in self.by_bot_ids[cid] if i > self.last_message_ids[cid]]  # чистим память

            for msg in messages:
                event = NewMessageEvent(self.__last_msg_event_tag, msg)
                result[cid].append(event)
        return result

    def parse_order_updates(self, obj) -> list[InitialOrderEvent | OrdersListChangedEvent | NewOrderEvent | OrderStatusChangedEvent]:
        """
        Парсит события, связанные с продажами.

        :param obj: Словарь из результата выполнения get_updates, где "type" == "orders_counters".
        :type obj: :obj:`dict`
        :return: Список событий, связанных с продажами.
        :rtype: :obj:`list[InitialOrderEvent | OrdersListChangedEvent | NewOrderEvent | OrderStatusChangedEvent]`
        """
        events = []
        self.__last_order_event_tag = obj.get("tag")
        if not self.__first_request:
            events.append(OrdersListChangedEvent(self.__last_order_event_tag,
                                                 obj["data"]["buyer"], obj["data"]["seller"]))
        if not self.order_requests:
            return events

        attempts = 3
        while attempts:
            attempts -= 1
            try:
                orders_list = self.account.get_sales()  # todo добавить возможность реакции на подтверждение очень старых заказов
                break
            except exceptions.RequestFailedError as e:
                logger.error(e)
            except:
                logger.error("Не удалось обновить список заказов.")
                logger.debug("TRACEBACK", exc_info=True)
            sleep(1)
        else:
            logger.error("Не удалось обновить список продаж: превышено кол-во попыток.")
            return events

        saved_orders = {}
        for order in orders_list[1]:
            saved_orders[order.id] = order
            if order.id not in self.saved_orders:
                if self.__first_request:
                    events.append(InitialOrderEvent(self.__last_order_event_tag, order))
                else:
                    events.append(NewOrderEvent(self.__last_order_event_tag, order))
                    if order.status == OrderStatuses.CLOSED:
                        events.append(OrderStatusChangedEvent(self.__last_order_event_tag, order))

            elif order.status != self.saved_orders[order.id].status:
                events.append(OrderStatusChangedEvent(self.__last_order_event_tag, order))
        self.saved_orders = saved_orders
        return events

    def update_chat_last_message(self, chat_id: int, message_id: int, message_text: str | None):
        """
        Обновляет сохраненный Айди последнего сообщения чата.

        :param chat_id: Айди чата.
        :type chat_id: :obj:`int`
        :param message_id: Айди сообщения.
        :type message_id: :obj:`int`
        :param message_text: Текст сообщения или :obj:`None`, если это изображение.
        :type message_text: :obj:`str` | :obj:`None`
        """
        self.chats_last_messages[chat_id] = {
            'node_msg_id': message_id,
            'user_msg_id': message_id,
            'last_msg_text': message_text
        }

    def mark_as_by_bot(self, chat_id: int, message_id: int):
        """
        Помечает сообщение с переданным айди, как отправленный с помощью :meth:`account.Account.send_message`.

        :param chat_id: Айди чата.
        :type chat_id: :obj:`int`
        :param message_id: Айди сообщения.
        :type message_id: :obj:`int`
        """
        if self.by_bot_ids.get(chat_id) is None:
            self.by_bot_ids[chat_id] = [message_id]
        else:
            self.by_bot_ids[chat_id].append(message_id)

    def listen(self, requests_delay: int | float = 6.0, ignore_exceptions: bool = True) -> Generator[
                   InitialChatEvent |
                   ChatsListChangedEvent |
                   LastChatMessageChangedEvent |
                   NewMessageEvent |
                   InitialOrderEvent |
                   OrdersListChangedEvent |
                   NewOrderEvent |
                   OrderStatusChangedEvent
               ]: # TODO remove
        """
        Бесконечно отправляет запросы для получения новых событий.

        :param requests_delay: Задержка между запросами (в секундах).
        :type requests_delay: :obj:`int` or :obj:`float`, опционально
        :param ignore_exceptions: Игнорировать ошибки?
        :type ignore_exceptions: :obj:`bool`, опционально
        :return: Генератор событий FunPay.
        :rtype: :obj:`Generator[InitialChatEvent | ChatsListChangedEvent | LastChatMessageChangedEvent | NewMessageEvent | InitialOrderEvent | OrdersListChangedEvent |
        NewOrderEvent | OrderStatusChangedEvent]`
        """
        while True:
            start_time = time()

            try:
                updates = self.get_updates()
                events = self.parse_updates(updates)
                for event in events: yield event

            except Exception as e:
                if not ignore_exceptions: raise e

                else:
                    logger.error("Произошла ошибка при получении событий. (ничего страшного, если это сообщение появляется нечасто).")
                    logger.debug("TRACEBACK", exc_info=True)


            iteration_time = time() - start_time

            if time() - self.account.last_429_err_time > 60:
                delay = requests_delay - iteration_time

                if delay > 0: sleep(delay)

            else: sleep(requests_delay)


__all__ = [
    'Runner'
]