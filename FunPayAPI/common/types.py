'В этом модуле описаны различные типы, датаклассы и перечисления FunPayAPI.'
from __future__ import annotations


from . import PRODUCTS_AMOUNT_RE, MessageTypes, Currencies, OrderStatuses, SubCategoryTypes, EventTypes, INVISIBLE_CHARACTER


import re
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from time import time
from typing import Literal, Self
import json


def get_message_type_by_re(text: str) -> MessageTypes:
    '''
    Возвращает тип сообщения на основе регулярных выражений.

    :param text: Текст сообщения.
    :type text: str
    :return: Тип сообщения.
    :rtype: MessageTypes
    '''
    for message_type in MessageTypes:
        if message_type is MessageTypes.NON_SYSTEM: continue


        if message_type.value.search(text): return message_type


    return MessageTypes.NON_SYSTEM


# ---------------------------------------------------------------------------- #
#                                  Датаклассы                                  #
# ---------------------------------------------------------------------------- #

# ------------------------------ Объекты FunPay ------------------------------ #
@dataclass(unsafe_hash=True)
class BuyerViewing:
    '''
    Класс, описывающий поле 'Покупатель смотрит'

    :param buyer_id: Айди покупателя.
    :type buyer_id: int
    :param link: Ссылка на лот, defaults to None.
    :type link: str | None, опционально
    :param text: Текстовое описание лота, defaults to None.
    :type text: str | None, опционально
    :param tag: Тег события, defaults to None.
    :type tag: str | None, опционально
    :param html: HTML-код блока просмотра, defaults to None.
    :type html: str | None, опционально
    '''
    buyer_id: int
    'Айди покупателя.'
    link: str | None = None
    'Ссылка на лот.'
    text: str | None = None
    'Текстовое описание лота.'
    tag: str | None = None
    'Тег события.'
    html: str | None = None
    'HTML-код блока просмотра.'


@dataclass(unsafe_hash=True)
class ChatShortcut:
    '''
    Класс, описывающий виджет чата со страницы https://funpay.com/chat/

    :param id: Айди чата.
    :type id: int
    :param name: Название чата (имя собеседника).
    :type name: str
    :param last_message_text: Текст последнего сообщения в чате (макс. 250 символов).
    :type last_message_text: str
    :param node_msg_id: Айди последнего сообщения в чате.
    :type node_msg_id: int
    :param user_msg_id: Айди последнего прочитанного сообщения.
    :type user_msg_id: int
    :param unread: Флаг непрочитанного чата.
    :type unread: bool
    :param html: HTML-код виджета чата.
    :type html: str
    :param last_by_bot: Отправлено ли последнее сообщение с помощью Account.send_message, defaults to None.
    :type last_by_bot: bool | None, опционально
    '''
    id: int
    'Айди чата.'
    name: str
    'Название чата (имя собеседника).'
    last_message_text: str
    'Текст последнего сообщения в чате (макс. 250 символов).'
    node_msg_id: int
    'Айди последнего сообщения в чате.'
    user_msg_id: int
    'Айди последнего прочитанного сообщения.'
    unread: bool
    'Флаг непрочитанного чата.'
    html: str
    'HTML-код виджета чата.'
    last_by_bot: bool | None = None
    'Отправлено ли последнее сообщение с помощью Account.send_message.'
    __last_message_type: MessageTypes | None = field(init=False, default=None)


    @property
    def last_message_type(self) -> MessageTypes:
        '''
        Тип последнего сообщения в чате на основе регулярных выражений.
        '''
        if self.__last_message_type is None: self.__last_message_type = get_message_type_by_re(self.last_message_text)


        return self.__last_message_type


@dataclass
class Chat:
    '''
    Класс, описывающий личный чат.

    :param id: Айди чата.
    :type id: int
    :param name: Название чата (имя собеседника).
    :type name: str
    :param html: HTML-код чата.
    :type html: str
    :param messages: Последние 100 сообщений чата, defaults to [].
    :type messages: list[Message], опционально
    :param looking_link: Ссылка на лот, который смотрит собеседник, defaults to None.
    :type looking_link: str | None, опционально
    :param looking_text: Название лота, который смотрит собеседник, defaults to None.
    :type looking_text: str | None, опционально
    '''
    id: int
    'Айди чата.'
    name: str
    'Название чата (имя собеседника).'
    html: str
    'HTML-код чата.'
    messages: list[Message] = field(default_factory=list)
    'Последние 100 сообщений чата.'
    looking_link: str | None = None
    'Ссылка на лот, который смотрит собеседник.'
    looking_text: str | None = None
    'Название лота, который смотрит собеседник.'


    def __hash__(self): return hash((self.id, self.name, self.html, self.looking_link, self.looking_text))


@dataclass(unsafe_hash=True)
class Message:
    '''
    Класс, описывающий отдельное сообщение.

    :param id: Айди сообщения.
    :type id: int
    :param text: Текст сообщения.
    :type text: str
    :param chat_id: Айди чата.
    :type chat_id: int | str
    :param chat_name: Название чата.
    :type chat_name: str | None
    :param interlocutor_id: Айди собеседника.
    :type interlocutor_id: int | None
    :param author: Автор сообщения.
    :type author: str | None
    :param author_id: Айди автора сообщения.
    :type author_id: int
    :param html: HTML-код сообщения.
    :type html: str
    :param buyer_viewing: Лот, который смотрит собеседник, defaults to None.
    :type buyer_viewing: BuyerViewing | None, опционально
    :param by_bot: Отправлено ли сообщение с помощью Account.send_message, defaults to False.
    :type by_bot: bool, опционально
    :param image_link: Ссылка на изображение в сообщении, defaults to None.
    :type image_link: str | None, опционально
    :param image_name: Название изображения, defaults to None.
    :type image_name: str | None, опционально
    :param badge: Текст бэйджика техподдержки или автовыдачи FunPay, defaults to None.
    :type badge: str | None, опционально
    :param is_employee: Является ли пользователь сотрудником, defaults to False.
    :type is_employee: bool, опционально
    :param is_support: Наличие бэйджика поддержки, defaults to False.
    :type is_support: bool, опционально
    :param is_moderation: Наличие бэйджика модерации, defaults to False.
    :type is_moderation: bool, опционально
    :param is_arbitration: Наличие бэйджика арбитража, defaults to False.
    :type is_arbitration: bool, опционально
    :param is_autoreply: Наличие бэйджика автоответа, defaults to False.
    :type is_autoreply: bool, опционально
    :param initiator_username: Ник пользователя, который выполнил действие (для системных сообщений), defaults to None.
    :type initiator_username: str | None, опционально
    :param initiator_id: Айди пользователя, который выполнил действие (для системных сообщений), defaults to None.
    :type initiator_id: int | None, опционально
    :param i_am_seller: Являемся ли мы продавцом по заказу (для системных сообщений), defaults to None.
    :type i_am_seller: bool | None, опционально
    :param i_am_buyer: Являемся ли мы покупателем по заказу (для системных сообщений), defaults to None.
    :type i_am_buyer: bool | None, опционально
    '''
    id: int
    'Айди сообщения.'
    text: str
    'Текст сообщения.'
    chat_id: int | str
    'Айди чата.'
    chat_name: str | None
    'Название чата.'
    interlocutor_id: int | None
    'Айди собеседника.'
    author: str | None
    'Автор сообщения.'
    author_id: int
    'Айди автора сообщения.'
    html: str
    'HTML-код сообщения.'
    buyer_viewing: BuyerViewing | None = None
    'Лот, который смотрит собеседник.'
    by_bot: bool = False
    'Отправлено ли сообщение с помощью Account.send_message.'
    image_link: str | None = None
    'Ссылка на изображение в сообщении.'
    image_name: str | None = None
    'Название изображения.'
    badge: str | None = None
    'Текст бэйджика техподдержки или автовыдачи FunPay.'
    is_employee: bool = False
    'Является ли пользователь сотрудником.'
    is_support: bool = False
    'Наличие бэйджика поддержки.'
    is_moderation: bool = False
    'Наличие бэйджика модерации.'
    is_arbitration: bool = False
    'Наличие бэйджика арбитража.'
    is_autoreply: bool = False
    'Наличие бэйджика автоответа.'
    initiator_username: str | None = None
    'Ник пользователя, который выполнил действие (для системных сообщений).'
    initiator_id: int | None = None
    'Айди пользователя, который выполнил действие (для системных сообщений).'
    i_am_seller: bool | None = None
    'Являемся ли мы продавцом по заказу (для системных сообщений).'
    i_am_buyer: bool | None = None
    'Являемся ли мы покупателем по заказу (для системных сообщений).'
    __type: MessageTypes | None = field(init=False, default=None)


    @property
    def type(self) -> MessageTypes:
        '''
        Тип сообщения.
        '''
        if self.__type is None:
            if self.author_id not in [0, 500]: self.__type = MessageTypes.NON_SYSTEM

            else: self.__type = get_message_type_by_re(self.text)


        return self.__type


@dataclass(unsafe_hash=True)
class OrderShortcut:
    '''
    Класс, описывающий виджет заказа со страницы https://funpay.com/orders/trade

    :param id: Айди заказа.
    :type id: str
    :param description: Описание заказа.
    :type description: str
    :param price: Цена заказа.
    :type price: float
    :param currency: Валюта заказа.
    :type currency: Currencies
    :param buyer_username: Никнейм покупателя.
    :type buyer_username: str
    :param buyer_id: Айди покупателя.
    :type buyer_id: int
    :param chat_id: Айди чата.
    :type chat_id: int | str
    :param status: Статус заказа.
    :type status: OrderStatuses
    :param date: Дата создания заказа.
    :type date: datetime
    :param subcategory_name: Название подкатегории, к которой относится заказ.
    :type subcategory_name: str
    :param subcategory: Подкатегория, к которой относится заказ.
    :type subcategory: SubCategory | None
    :param html: HTML-код виджета заказа.
    :type html: str
    '''
    id: str
    'Айди заказа.'
    description: str
    'Описание заказа.'
    price: float
    'Цена заказа.'
    currency: Currencies
    'Валюта заказа.'
    buyer_username: str
    'Никнейм покупателя.'
    buyer_id: int
    'Айди покупателя.'
    chat_id: int | str
    'Айди чата.'
    status: OrderStatuses
    'Статус заказа.'
    date: datetime
    'Дата создания заказа.'
    subcategory_name: str
    'Название подкатегории, к которой относится заказ.'
    subcategory: SubCategory | None
    'Подкатегория, к которой относится заказ.'
    html: str
    'HTML-код виджета заказа.'
    __amount: int | None = field(init=False, default=None)


    @property
    def amount(self) -> int:
        '''
        Кол-во товаров (ищет по регулярному выражению).
        '''
        if self.__amount is None:
            result = [m.groupdict() for m in PRODUCTS_AMOUNT_RE.finditer(self.description)]

            self.__amount = int(result[0]['amount'].replace(' ', '')) if result else 1


        return self.__amount


@dataclass
class Order:
    '''
    Класс, описывающий заказ со страницы https://funpay.com/orders/<ORDER_ID>/

    :param id: Айди заказа.
    :type id: str
    :param status: Статус заказа.
    :type status: OrderStatuses
    :param subcategory: Подкатегория заказа.
    :type subcategory: SubCategory | None
    :param lot_params: Параметры лота (значения некоторых полей заказа).
    :type lot_params: list[tuple[str, str]]
    :param buyer_params: Параметры заказа, указанные покупателем.
    :type buyer_params: dict[str, str]
    :param title: Краткое описание (название) заказа. То же самое, что и title.
    :type title: str | None
    :param short_description: Краткое описание (название) заказа. То же самое, что и short_description.
    :type short_description: str | None
    :param full_description: Полное описание заказа.
    :type full_description: str | None
    :param amount: Количество.
    :type amount: int
    :param sum: Сумма заказа.
    :type sum: float
    :param currency: Валюта заказа.
    :type currency: Currencies
    :param buyer_id: Айди покупателя.
    :type buyer_id: int
    :param buyer_username: Никнейм покупателя.
    :type buyer_username: str
    :param seller_id: Айди продавца.
    :type seller_id: int
    :param seller_username: Никнейм продавца.
    :type seller_username: str
    :param chat_id: Айди чата.
    :type chat_id: str | int
    :param html: HTML-код заказа.
    :type html: str
    :param review: Объект отзыва заказа.
    :type review: Review | None
    :param order_secrets: Список товаров автовыдачи FunPay заказа.
    :type order_secrets: list[str]
    '''
    id: str
    'Айди заказа.'
    status: OrderStatuses
    'Статус заказа.'
    subcategory: SubCategory | None
    'Подкатегория заказа.'
    lot_params: list[tuple[str, str]]
    'Параметры лота (значения некоторых полей заказа).'
    buyer_params: dict[str, str]
    'Параметры заказа, указанные покупателем.'
    title: str | None
    'Краткое описание (название) заказа. То же самое, что и title.'
    short_description: str | None
    'Краткое описание (название) заказа. То же самое, что и short_description.'
    full_description: str | None
    'Полное описание заказа.'
    amount: int
    'Количество.'
    sum: float
    'Сумма заказа.'
    currency: Currencies
    'Валюта заказа.'
    buyer_id: int
    'Айди покупателя.'
    buyer_username: str
    'Никнейм покупателя.'
    seller_id: int
    'Айди продавца.'
    seller_username: str
    'Никнейм продавца.'
    chat_id: str | int
    'Айди чата.'
    html: str
    'HTML-код заказа.'
    review: Review | None
    'Объект отзыва заказа.'
    order_secrets: list[str]
    'Список товаров автовыдачи FunPay заказа.'


    @property
    def lot_params_dict(self) -> dict[str, str]:
        '''
        Параметры лота из заказа в виде словаря.

        ВАЖНО!!! Если названия дублируются - часть данных будет утеряна.
        '''
        return {k: v for k, v in self.lot_params}


    def get_buyer_param(self, *args: str) -> str | None:
        '''
        Возвращает параметр, введенный покупателем по его названию.

        :return: Значение параметра.
        :rtype: str | None
        '''
        for param_name in args:
            if param_name in self.buyer_params: return self.buyer_params[param_name]


    def __hash__(self): return hash(
        (
            self.id,
            self.status,
            self.subcategory,
            self.title,
            self.short_description,
            self.full_description,
            self.amount,
            self.sum,
            self.currency,
            self.buyer_id,
            self.buyer_username,
            self.seller_id,
            self.seller_username,
            self.chat_id,
            self.html,
            self.review
        )
    )


@dataclass
class Category:
    '''
    Класс, описывающий категорию (игру).

    :param id: Айди категории (game_id/data-id).
    :type id: int
    :param name: Название категории (игры).
    :type name: str
    :param subcategories: Список подкатегорий, defaults to [].
    :type subcategories: list[SubCategory], опционально
    :param position: Порядковый номер игры в списке игр (по алфавиту), defaults to 100_000.
    :type position: int, опционально
    '''
    id: int
    'Айди категории (game_id/data-id).'
    name: str
    'Название категории (игры).'
    subcategories: list[SubCategory] = field(default_factory=list)
    'Список подкатегорий.'
    position: int = 100_000
    'Порядковый номер игры в списке игр (по алфавиту).'


    @property
    def sorted_subcategories(self) -> dict[SubCategoryTypes, dict[int, SubCategory]]:
        '''
        Все подкатегории данной категории (игры) в виде словаря {Тип: {Айди: Подкатегория}}.
        '''
        sorted_subcategories: dict[SubCategoryTypes, dict[int, SubCategory]] = {
            SubCategoryTypes.COMMON: {},
            SubCategoryTypes.CURRENCY: {}
        }

        for subcategory in self.subcategories: sorted_subcategories[subcategory.type][subcategory.id] = subcategory


        return sorted_subcategories


    def add_subcategory(self, subcategory: SubCategory):
        '''
        Добавляет подкатегорию в список подкатегорий.

        :param subcategory: Объект подкатегории.
        :type subcategory: SubCategory
        '''
        if subcategory not in self.subcategories: self.subcategories.append(subcategory)


    def get_subcategory(self, subcategory_type: SubCategoryTypes, subcategory_id: int) -> SubCategory | None:
        '''
        Возвращает объект подкатегории.

        :param subcategory_type: Тип подкатегории.
        :type subcategory_type: SubCategoryTypes
        :param subcategory_id: Айди подкатегории.
        :type subcategory_id: int
        :return: Объект подкатегории.
        :rtype: SubCategory | None
        '''
        return self.sorted_subcategories[subcategory_type].get(subcategory_id)


    def __hash__(self): return hash((self.id, self.name, self.position))


@dataclass(unsafe_hash=True)
class SubCategory:
    '''
    Класс, описывающий подкатегорию.

    :param id: Айди подкатегории.
    :type id: int
    :param name: Название подкатегории.
    :type name: str
    :param type: Тип подкатегории.
    :type type: SubCategoryTypes
    :param category: Родительская категория (игра).
    :type category: Category
    :param position: Порядковый номер подкатегории в общем списке игр (для сортировки), defaults to 100_000.
    :type position: int, опционально
    '''
    id: int
    'Айди подкатегории.'
    name: str
    'Название подкатегории.'
    type: SubCategoryTypes
    'Тип подкатегории.'
    category: Category
    'Родительская категория (игра).'
    position: int = 100_000
    'Порядковый номер подкатегории в общем списке игр (для сортировки).'


    @property
    def fullname(self) -> str:
        'Полное название подкатегории.'
        return f'{self.name} {self.category.name}'


    @property
    def public_link(self) -> str:
        '''
        Публичная ссылка на список лотов подкатегории.
        '''
        return f'https://funpay.com/{'chips' if self.type is SubCategoryTypes.CURRENCY else 'lots'}/{self.id}/'


    @property
    def private_link(self) -> str:
        '''
        Приватная ссылка на список лотов подкатегории (для редактирования лотов).
        '''
        return f'{self.public_link}trade'


@dataclass
class __Fields:
    fields: dict[str, str]
    'Поля лота.'


    @property
    def csrf_token(self) -> str | None:
        'CSRF-токен.'
        return self.fields.get('csrf_token')

    @csrf_token.setter
    def csrf_token(self, csrf_token: str | None): self.fields['csrf_token'] = csrf_token if csrf_token is not None else ''


@dataclass
class LotFields(__Fields):
    '''
    Класс, описывающий поля лота со страницы редактирования лота.

    :param fields: Поля лота.
    :type fields: dict[str, str]
    :param lot_id: Айди лота.
    :type lot_id: int
    :param subcategory: Подкатегория лота, defaults to None.
    :type subcategory: SubCategory | None, опционально
    :param currency: Валюта лота, defaults to Currencies.UNKNOWN.
    :type currency: Currencies, опционально
    :param calc_result: Ответ на запрос о рассчете комиссии раздела, defaults to None.
    :type calc_result: CalcResult | None, опционально
    '''
    lot_id: int
    'Айди лота.'
    subcategory: SubCategory | None = None
    'Подкатегория лота.'
    currency: Currencies = Currencies.UNKNOWN
    'Валюта лота.'
    calc_result: CalcResult | None = None
    'Ответ на запрос о рассчете комиссии раздела.'


    @property
    def title_ru(self) -> str:
        '''
        Русское краткое описание (название) лота.
        '''
        return self.fields.get('fields[summary][ru]', '')

    @title_ru.setter
    def title_ru(self, title_ru: str): self.fields['fields[summary][ru]'] = title_ru


    @property
    def title_en(self) -> str:
        '''
        Английское краткое описание (название) лота.
        '''
        return self.fields.get('fields[summary][en]', '')

    @title_en.setter
    def title_en(self, title_en: str): self.fields['fields[summary][en]'] = title_en


    @property
    def description_ru(self) -> str:
        '''
        Русское полное описание лота.
        '''
        return self.fields.get('fields[desc][ru]', '')

    @description_ru.setter
    def description_ru(self, description_ru: str): self.fields['fields[desc][ru]'] = description_ru


    @property
    def description_en(self) -> str:
        '''
        Английское полное описание лота.
        '''
        return self.fields.get('fields[desc][en]', '')

    @description_en.setter
    def description_en(self, description_en: str): self.fields['fields[desc][en]'] = description_en


    @property
    def payment_msg_ru(self) -> str:
        '''
        Русское сообщение покупателю после оплаты.
        '''
        return self.fields.get('fields[payment_msg][ru]', '')

    @payment_msg_ru.setter
    def payment_msg_ru(self, payment_msg_ru: str): self.fields['fields[payment_msg][ru]'] = payment_msg_ru


    @property
    def payment_msg_en(self) -> str:
        '''
        Английское сообщение покупателю после оплаты.
        '''
        return self.fields.get('fields[payment_msg][en]', '')

    @payment_msg_en.setter
    def payment_msg_en(self, payment_msg_en: str): self.fields['fields[payment_msg][en]'] = payment_msg_en


    @property
    def images(self) -> list[int]:
        '''
        Айди изображений лота.
        '''
        return [int(image) for image in self.fields.get('fields[images]', '').split(',') if image]

    @images.setter
    def images(self, images: list[int]): self.fields['fields[images]'] = ','.join([str(image) for image in images])


    @property
    def auto_delivery(self) -> bool:
        '''
        Включена ли автовыдача FunPay.
        '''
        return self.fields.get('auto_delivery') == 'on'

    @auto_delivery.setter
    def auto_delivery(self, auto_delivery: bool): self.fields['auto_delivery'] = 'on' if auto_delivery else ''


    @property
    def secrets(self) -> list[str]:
        '''
        Товары автовыдачи FunPay.
        '''
        return [secret for secret in self.fields.get('secrets', '').strip().split('\n') if secret]

    @secrets.setter
    def secrets(self, secrets: list[str]): self.fields['secrets'] = '\n'.join(secrets)


    @property
    def amount(self) -> int | None:
        '''
        Кол-во товара.
        '''
        return int(self.fields.get('amount')) if self.fields.get('amount') else None

    @amount.setter
    def amount(self, amount: int | None): self.fields['amount'] = str(amount) if amount is not None else ''


    @property
    def price(self) -> float | None:
        '''
        Цена за 1 шт.
        '''
        return float(price) if (price := self.fields.get('price')) else None

    @price.setter
    def price(self, price: float | None): self.fields['price'] = str(price) if price is not None else ''


    @property
    def active(self) -> bool:
        '''
        Активен ли лот.
        '''
        return self.fields.get('active') == 'on'

    @active.setter
    def active(self, active: bool): self.fields['active'] = 'on' if active else ''


    @property
    def deactivate_after_sale(self) -> bool:
        '''
        Деактивировать ли лот после продажи.
        '''
        return self.fields.get('deactivate_after_sale') == 'on'

    @deactivate_after_sale.setter
    def deactivate_after_sale(self, deactivate_after_sale: bool): self.fields['deactivate_after_sale'] = 'on' if deactivate_after_sale else ''


    @property
    def public_link(self) -> str:
        '''
        Публичная ссылка на лот.
        '''
        return f'https://funpay.com/lots/offer?id={self.lot_id}'


    @property
    def private_link(self) -> str:
        '''
        Приватная ссылка на лот (на изменение лота).
        '''
        return f'https://funpay.com/lots/offerEdit?offer={self.lot_id}'


    def __hash__(self): return hash((self.lot_id, self.subcategory, self.currency, self.calc_result))


@dataclass(unsafe_hash=True)
class ChipOffer:
    '''
    Класс, описывающий секцию полей лота валюты (предложение).

    :param lot_id: Айди лота.
    :type lot_id: str
    :param active: Активен ли лот, defaults to False.
    :type active: bool, опционально
    :param server: Сервер (игра), defaults to None.
    :type server: str | None, опционально
    :param side: , defaults to None.
    :type side: str | None, опционально
    :param price: Цена, defaults to None.
    :type price: float | None, опционально
    :param amount: Кол-во доступной валюты, defaults to None.
    :type amount: int | None, опционально
    '''
    lot_id: str
    'Айди лота.'
    active: bool = False
    'Активен ли лот.'
    server: str | None = None
    'Сервер (игра).'
    side: str | None = None
    '' # TODO
    price: float | None = None
    'Цена.'
    amount: int | None = None
    'Кол-во доступной валюты.'


    @property
    def key(self):
        s = ''.join([f'[{key}]' for key in self.lot_id.split('-')[3:]])
        return f'offers{s}'


@dataclass
class ChipFields(__Fields):
    '''
    Класс, описывающий поля лота со страницы редактирования лота валюты.

    :param fields: Поля лота.
    :type fields: dict[str, str]
    :param account_id: Айди аккаунта FunPay.
    :type account_id: int
    :param subcategory_id: Айди подкатегории лота.
    :type subcategory_id: int
    '''
    account_id: int
    'Айди аккаунта FunPay.'
    subcategory_id: int
    'Айди подкатегории лота.'
    __chip_offers: dict[str, ChipOffer] = field(init=False, default_factory=dict)


    @property
    def min_sum(self) -> float | None:
        'Минимальное кол-во для покупки.'
        return float(self.fields.get('options[chip_min_sum]')) if self.fields.get('options[chip_min_sum]') else None

    @min_sum.setter
    def min_sum(self, min_sum: float | None): self.fields['options[chip_min_sum]'] = min_sum if min_sum else None


    @property
    def game_id(self) -> int:
        'Айди игры'
        return int(self.fields.get('game'))

    @game_id.setter
    def game_id(self, game_id: int): self.fields['game'] = str(game_id)


    @property
    def chip_offers(self) -> dict[str, ChipOffer]:
        'Секции (предложения) валюты.'
        if not self.__chip_offers:
            self.__chip_offers: dict[str, ChipOffer] = {}

            for k in self.fields:
                if not k.startswith('offers'): continue


                nums = re.findall(r'\d+', k)
                key = '-'.join(list(map(str, nums)))

                offer_id = f'{self.account_id}-{self.game_id}-{self.subcategory_id}-{key}'

                if offer_id not in self.__chip_offers: self.__chip_offers[offer_id] = ChipOffer(offer_id)


                field = k.split('[')[-1].rstrip(']')

                v = self.fields[k]

                if field == 'active': self.__chip_offers[offer_id].active = v == 'on'
                elif field == 'price': self.__chip_offers[offer_id].price = float(v) if v else None
                elif field == 'amount': self.__chip_offers[offer_id].amount = int(v) if v else None


        return self.__chip_offers


    @chip_offers.setter
    def chip_offers(self, chip_offers: dict[str, ChipOffer]):
        self.__chip_offers = {}


        for chip_offer in chip_offers.values():
            key = chip_offer.key

            self.fields[f'{key}[amount]'] = str(chip_offer.amount) if chip_offer.amount is not None else ''

            self.fields[f'{key}[price]'] = str(chip_offer.price) if chip_offer.price is not None else ''

            if chip_offer.active: self.fields[f'{key}[active]'] = 'on'

            else: self.fields.pop(f'{key}[active]', None)


    def __hash__(self): return hash((self.account_id, self.subcategory_id))


@dataclass
class LotPage:
    '''
    Класс, описывающий поля лота со страницы лота (https://funpay.com/lots/offer?id=XXXXXXXXXX).

    :param lot_id: Айди лота.
    :type lot_id: int
    :param subcategory: Подкатегория.
    :type subcategory: SubCategory | None
    :param short_description: Краткое описание.
    :type short_description: str | None
    :param full_description: Подробное описание.
    :type full_description: str | None
    :param image_urls: Список URL-адресов изображений лота.
    :type image_urls: list[str]
    :param seller_id: Айди продавца.
    :type seller_id: int
    :param seller_username: Имя продавца.
    :type seller_username: str
    '''
    lot_id: int
    'Айди лота.'
    subcategory: SubCategory | None
    'Подкатегория.'
    short_description: str | None
    'Краткое описание.'
    full_description: str | None
    'Подробное описание.'
    image_urls: list[str]
    'Список URL-адресов изображений лота.'
    seller_id: int
    'Айди продавца.'
    seller_username: str
    'Имя продавца.'


    @property
    def seller_url(self) -> str:
        '''
        Cсылка на продавца.
        '''
        return f'https://funpay.com/users/{self.seller_id}/'


    def __hash__(self): return hash((self.lot_id, self.subcategory, self.short_description, self.full_description, self.seller_id, self.seller_username))


@dataclass(unsafe_hash=True)
class SellerShortcut:
    '''
    Класс, описывающий объект пользователя из таблицы предложений.

    :param id: Айди пользователя.
    :type id: int
    :param username: Никнейм пользователя.
    :type username: str
    :param online: Онлайн ли пользователь.
    :type online: bool
    :param stars: Количество звезд.
    :type stars: int | None
    :param reviews: Количество отзывов.
    :type reviews: int
    :param html: HTML-код страницы пользователя.
    :type html: str
    '''
    id: int
    'Айди пользователя.'
    username: str
    'Никнейм пользователя.'
    online: bool
    'Онлайн ли пользователь.'
    stars: int | None
    'Количество звезд.'
    reviews: int
    'Количество отзывов.'
    html: str
    'HTML-код страницы пользователя.'


    @property
    def link(self):
        '''
        Cсылка на продавца.
        '''
        return f'https://funpay.com/users/{self.id}/'


@dataclass
class LotShortcut:
    '''
    Класс, описывающий виджет лота.

    :param id: Айди лота.
    :type id: int | str
    :param server: Название сервера (если указан).
    :type server: str | None
    :param side: Сторона (если указана).
    :type side: str | None
    :param title: Краткое описание (название) лота.
    :type title: str | None
    :param description: Краткое описание (название) лота.
    :type description: str | None
    :param amount: Количество
    :type amount: int | None
    :param price: Цена лота.
    :type price: float
    :param currency: Валюта лота.
    :type currency: Currencies
    :param subcategory: Подкатегория лота.
    :type subcategory: SubCategory | None
    :param seller: Объект продавца (только для лотов из талицы).
    :type seller: SellerShortcut | None
    :param auto: Включена ли автовыдача FunPay у лота?
    :type auto: bool
    :param promo: В закрепе ли лот? (только для лотов из таблицы)
    :type promo: bool | None
    :param attributes: Атрибуты лота (только для лотов из таблицы)
    :type attributes: dict[str, int | str] | None
    :param html: HTML-код виджета лота.
    :type html: str
    '''
    id: int | str
    'Айди лота.'
    server: str | None
    'Название сервера (если указан).'
    side: str | None
    'Сторона (если указана).'
    title: str | None
    'Краткое описание (название) лота.'
    description: str | None
    'Краткое описание (название) лота.'
    amount: int | None
    'Количество'
    price: float
    'Цена лота.'
    currency: Currencies
    'Валюта лота.'
    subcategory: SubCategory | None
    'Подкатегория лота.'
    seller: SellerShortcut | None
    'Объект продавца (только для лотов из талицы).'
    auto: bool
    'Включена ли автовыдача FunPay у лота?'
    promo: bool | None
    'В закрепе ли лот? (только для лотов из таблицы)'
    attributes: dict[str, int | str] | None
    'Атрибуты лота (только для лотов из таблицы)'
    html: str
    'HTML-код виджета лота.'


    @property
    def public_link(self) -> str:
        '''
        Публичная ссылка на лот.
        '''
        return f'https://funpay.com/{'chips' if self.subcategory.type is SubCategoryTypes.CURRENCY else 'lots'}/offer?id={self.id}'


    def __hash__(self): return hash(
                (
                    self.id,
                    self.server,
                    self.side,
                    self.title,
                    self.description,
                    self.amount,
                    self.price,
                    self.currency,
                    self.subcategory,
                    self.seller,
                    self.auto,
                    self.promo,
                    self.html
                )
    )


@dataclass(unsafe_hash=True)
class MyLotShortcut:
    '''
    Класс, описывающий виджет лота со страницы https://funpay.com/lots/{айди_подкатегории}/trade.

    :param id: Айди лота.
    :type id: int | str
    :param server: Название сервера (если указан).
    :type server: str | None
    :param side: Сторона (если указана).
    :type side: str | None
    :param title: Краткое описание (название) лота.
    :type title: str | None
    :param description: Краткое описание (название) лота.
    :type description: str | None
    :param amount: Количество
    :type amount: int | None
    :param price: Цена лота.
    :type price: float
    :param currency: Валюта лота.
    :type currency: Currencies
    :param subcategory: Подкатегория лота.
    :type subcategory: SubCategory | None
    :param auto: Включена ли автовыдача FunPay у лота.
    :type auto: bool
    :param active: Активен ли лот?
    :type active: bool
    :param html: HTML-код виджета лота.
    :type html: str
    '''
    id: int | str
    'Айди лота.'
    server: str | None
    'Название сервера (если указан).'
    side: str | None
    'Сторона (если указана).'
    title: str | None
    'Краткое описание (название) лота.'
    description: str | None
    'Краткое описание (название) лота.'
    amount: int | None
    'Количество'
    price: float
    'Цена лота.'
    currency: Currencies
    'Валюта лота.'
    subcategory: SubCategory | None
    'Подкатегория лота.'
    auto: bool
    'Включена ли автовыдача FunPay у лота.'
    active: bool
    'Активен ли лот?'
    html: str
    'HTML-код виджета лота.'


    @property
    def public_link(self) -> str:
        '''
        Публичная ссылка на лот.
        '''
        return f'https://funpay.com/{'chips' if self.subcategory.type is SubCategoryTypes.CURRENCY else 'lots'}/offer?id={self.id}'


@dataclass(unsafe_hash=True)
class UserProfile:
    '''
    Класс, описывающий пользователя FunPay.

    :param id: Айди пользователя.
    :type id: int
    :param username: Никнейм пользователя.
    :type username: str
    :param profile_photo: Ссылка на фото профиля.
    :type profile_photo: str
    :param online: Онлайн ли пользователь.
    :type online: bool
    :param banned: Заблокирован ли пользователь.
    :type banned: bool
    :param html: HTML код страницы пользователя.
    :type html: str
    '''
    id: int
    'Айди пользователя.'
    username: str
    'Никнейм пользователя.'
    profile_photo: str
    'Ссылка на фото профиля.'
    online: bool
    'Онлайн ли пользователь.'
    banned: bool
    'Заблокирован ли пользователь.'
    html: str
    'HTML код страницы пользователя.'
    __lots: dict[int | str, LotShortcut] = field(init=False, default_factory=dict)
    __sorted_by_subcategory_lots: dict[SubCategory, dict[int | str, LotShortcut]] = field(init=False, default_factory=dict)
    __sorted_by_subcategory_type_lots: dict[SubCategoryTypes, dict[int | str, LotShortcut]] = field(init=False, default_factory=dict)


    @property
    def lots(self) -> list[LotShortcut]:
        '''
        Список всех лотов пользователя.
        '''
        return list(self.__lots.values())


    @property
    def lots_dict(self) -> dict[int | str, LotShortcut]:
        '''
        Все лоты пользователя в виде словаря {Айди: лот}}.
        '''
        return self.__lots


    @property
    def sorted_by_subcategory_lots(self) -> dict[SubCategory, dict[int | str, LotShortcut]]:
        '''
        Все лоты пользователя в виде словаря {подкатегория: {Айди: лот}}.
        '''
        return self.__sorted_by_subcategory_lots


    @property
    def sorted_by_subcategory_type_lots(self) -> dict[SubCategoryTypes, dict[int | str, LotShortcut]]:
        '''
        Все лоты пользователя в виде словаря {Тип подкатегории: {Айди: лот}}.
        '''
        if not self.__sorted_by_subcategory_type_lots: self.__sorted_by_subcategory_type_lots = {
            SubCategoryTypes.COMMON: {},
            SubCategoryTypes.CURRENCY: {}
        }


        return self.__sorted_by_subcategory_type_lots


    def get_lot(self, lot_id: int | str) -> LotShortcut | None:
        '''
        Возвращает объект лота со страницы пользователя.

        :param lot_id: Айди лота.
        :type lot_id: int | str

        :return: Объект лота со страницы пользователя.
        :rtype: LotShortcut | None
        '''
        if isinstance(lot_id, str) and lot_id.isnumeric(): return self.__lots.get(int(lot_id))


        return self.__lots.get(lot_id)


    def update_lot(self, lot: LotShortcut) -> None:
        '''
        Обновляет лот в списке лотов.

        :param lot: Объект лота.
        :type lot: LotShortcut
        '''
        self.__lots[lot.id] = lot


        if lot.subcategory not in self.sorted_by_subcategory_lots: self.__sorted_by_subcategory_lots[lot.subcategory] = {}

        self.__sorted_by_subcategory_lots[lot.subcategory][lot.id] = lot


        if not self.__sorted_by_subcategory_type_lots: self.__sorted_by_subcategory_type_lots = {
            SubCategoryTypes.COMMON: {},
            SubCategoryTypes.CURRENCY: {}
        }

        self.__sorted_by_subcategory_type_lots[lot.subcategory.type][lot.id] = lot


    def add_lot(self, lot: LotShortcut) -> None:
        '''
        Добавляет лот в список лотов.

        :param lot: Объект лота.
        :type lot: LotShortcut
        '''
        if lot.id in self.lots_dict: return

        self.update_lot(lot)


    @property
    def common_lots(self) -> list[LotShortcut]:
        '''
        Возвращает список стандартных лотов со страницы пользователя.
        '''
        return list(self.sorted_by_subcategory_type_lots[SubCategoryTypes.COMMON].values())


    @property
    def currency_lots(self) -> list[LotShortcut]:
        '''
        Возвращает список лотов-валют со страницы пользователя.
        '''
        return list(self.sorted_by_subcategory_type_lots[SubCategoryTypes.CURRENCY].values())


@dataclass(unsafe_hash=True)
class Review:
    '''
    Класс, описывающий отзыв на заказ.

    :param stars: Кол-во звезде в отзыве.
    :type stars: int | None
    :param text: Текст отзыва.
    :type text: str | None
    :param reply: Текст ответа на отзыв.
    :type reply: str | None
    :param anonymous: Анонимный ли отзыв.
    :type anonymous: bool
    :param html: HTML код отзыва.
    :type html: str
    :param hidden: Скрыт ли отзыв.
    :type hidden: bool
    :param order_id: Айди заказа, к которому относится отзыв, defaults to None.
    :type order_id: str | None, опционально
    :param author: Автор отзыва, defaults to None.
    :type author: str | None, опционально
    :param author_id: Айди автора отзыва, defaults to None.
    :type author_id: int | None, опционально
    :param by_bot: Оставлен ли отзыв ботом, defaults to False.
    :type by_bot: bool, опционально
    :param reply_by_bot: Оставлен ли ответ на отзыв ботом, defaults to False.
    :type reply_by_bot: bool, опционально
    '''
    stars: int | None
    'Кол-во звезде в отзыве.'
    text: str | None
    'Текст отзыва.'
    reply: str | None
    'Текст ответа на отзыв.'
    anonymous: bool
    'Анонимный ли отзыв?'
    html: str
    'HTML код отзыва.'
    hidden: bool
    'Скрыт ли отзыв?'
    order_id: str | None = None
    'Айди заказа, к которому относится отзыв.'
    author: str | None = None
    'Автор отзыва.'
    author_id: int | None = None
    'Айди автора отзыва.'
    by_bot: bool = False
    'Оставлен ли отзыв ботом.'
    reply_by_bot: bool = False
    'Оставлен ли ответ на отзыв ботом.'


@dataclass(unsafe_hash=True)
class Balance:
    '''
    Класс, описывающий информацию о балансе аккаунта.

    :param total_rub: Общий рублёвый баланс.
    :type total_rub: float
    :param available_rub: Доступный к выводу рублёвый баланс.
    :type available_rub: float
    :param total_usd: Общий долларовый баланс.
    :type total_usd: float
    :param available_usd: Доступный к выводу долларовый баланс.
    :type available_usd: float
    :param total_eur: Общий евро баланс.
    :type total_eur: float
    :param available_eur: Доступный к выводу евро баланс.
    :type available_eur: float
    '''
    total_rub: float
    'Общий рублёвый баланс.'
    available_rub: float
    'Доступный к выводу рублёвый баланс.'
    total_usd: float
    'Общий долларовый баланс.'
    available_usd: float
    'Доступный к выводу долларовый баланс.'
    total_eur: float
    'Общий евро баланс.'
    available_eur: float
    'Доступный к выводу евро баланс.'


@dataclass(unsafe_hash=True)
class PaymentMethod:
    '''
    Класс, описывающий платежное средство при рассчете цены для покупателя.

    :param name: Название.
    :type name: str | None
    :param price: Цена (с комиссией).
    :type price: float
    :param currency: Валюта.
    :type currency: Currencies
    :param position: Позиция для сортировки.
    :type position: int | None
    '''
    name: str | None
    'Название.'
    price: float
    'Цена (с комиссией).'
    currency: Currencies
    'Валюта.'
    position: int | None
    'Позиция для сортировки.'


@dataclass
class CalcResult:
    '''
    Класс, описывающий ответ на запрос о рассчете комиссии раздела.

    :param subcategory_type: Тип подкатегории.
    :type subcategory_type: SubCategoryTypes
    :param subcategory_id: Айди подкатегории.
    :type subcategory_id: int
    :param methods: Список платежных средств.
    :type methods: list[PaymentMethod]
    :param price: Цена без комиссии.
    :type price: float
    :param min_price_with_commission: Минимальная цена с комиссией из ответа FunPay, наличие не обязательно.
    :type min_price_with_commission: float | None
    :param min_price_currency: Валюта минимальной цены.
    :type min_price_currency: Currencies
    :param account_currency: Валюта аккаунта.
    :type account_currency: Currencies
    '''
    subcategory_type: SubCategoryTypes
    'Тип подкатегории.'
    subcategory_id: int
    'Айди подкатегории.'
    methods: list[PaymentMethod]
    'Список платежных средств.'
    price: float
    'Цена без комиссии.'
    min_price_with_commission: float | None
    'Минимальная цена с комиссией из ответа FunPay, наличие не обязательно.'
    min_price_currency: Currencies
    'Валюта минимальной цены.'
    account_currency: Currencies
    'Валюта аккаунта.'


    def get_coefficient(self, currency: Currencies) -> float:
        '''
        Отношение цены с комиссией в переданной валюте к цене без комиссии в валюте аккаунта.

        :param currency: Валюта.
        :type currency: Currencies
        :raises Exception: При ошибке определения коэффициента комиссии.
        :return: Коэффициент комиссии.
        :rtype: float
        '''
        if self.min_price_with_commission and (currency == self.min_price_currency == self.account_currency): return self.min_price_with_commission / self.price

        else:
            res = min(filter(lambda x: x.currency == currency, self.methods), key=lambda x: x.price, default=None)

            if not res: raise Exception('Невозможно определить коэффициент комиссии.') # TODO Custom Exception

            return res.price / self.price


    @property
    def commission_coefficient(self) -> float:
        '''
        Отношение цены с комиссией к цене без комиссии в валюте аккаунта.
        '''
        return self.get_coefficient(self.account_currency)


    @property
    def commission_percent(self) -> float:
        '''
        Процент комиссии.
        '''
        return (self.commission_coefficient - 1) * 100


    def __hash__(self): return hash((self.subcategory_type, self.subcategory_id, self.price, self.min_price_with_commission, self.min_price_currency, self.account_currency))


# ------------------------------ События FunPay ------------------------------ #
@dataclass
class BaseEvent:
    '''
    Базовый класс события.

    :param runner_tag: Тег Runner'а.
    :type runner_tag: str
    :param type: Тип события.
    :type type: EventTypes
    '''
    runner_tag: str
    'Тег Runner\'а.'
    type: EventTypes
    'Тип события.'
    event_time: int | float = field(init=False, default_factory=time)
    'Время события.'


@dataclass(unsafe_hash=True)
class InitialChatEvent(BaseEvent):
    '''
    Класс события: обнаружен чат при первом запросе Runner'а.

    :param runner_tag: Тег Runner'а.
    :type runner_tag: str
    :param cha: Объект обнаруженного чата.
    :type chat: ChatShortcut
    '''
    type: EventTypes = field(init=False, default=EventTypes.INITIAL_CHAT)
    'Тип события.'
    chat: ChatShortcut
    'Объект обнаруженного чата.'


@dataclass(unsafe_hash=True)
class ChatsListChangedEvent(BaseEvent): # TODO: добавить список всех чатов.
    '''
    Класс события: список чатов и / или содержимое одного / нескольких чатов изменилось.

    :param runner_tag: Тег Runner'а.
    :type runner_tag: str
    '''
    type: EventTypes = field(init=False, default=EventTypes.CHATS_LIST_CHANGED)
    'Тип события.'


@dataclass(unsafe_hash=True)
class LastChatMessageChangedEvent(BaseEvent):
    '''
    Класс события: последнее сообщение в чате изменилось.

    :param runner_tag: Тег Runner'а.
    :type runner_tag: str
    :param chat: Объект чата, в котором изменилось последнее сообщение.
    :type chat: ChatShortcut
    '''
    type: EventTypes = field(init=False, default=EventTypes.LAST_CHAT_MESSAGE_CHANGED)
    'Тип события.'
    chat: ChatShortcut
    'Объект чата, в котором изменилось последнее сообщение.'


@dataclass
class NewMessageEvent(BaseEvent):
    '''
    Класс события: в истории чата обнаружено новое сообщение.

    :param runner_tag: Тег Runner'а.
    :type runner_tag: str
    :param message: Объект нового сообщения.
    :type message: Message
    '''
    type: EventTypes = field(init=False, default=EventTypes.NEW_MESSAGE)
    'Тип события.'
    message: Message
    'Объект нового сообщения.'


@dataclass(unsafe_hash=True)
class InitialOrderEvent(BaseEvent):
    '''
    Класс события: обнаружен заказ при первом запросе Runner'а.

    :param runner_tag: Тег Runner'а.
    :type runner_tag: str
    :param order: Объект обнаруженного заказа.
    :type order: OrderShortcut
    '''
    type: EventTypes = field(init=False, default=EventTypes.INITIAL_ORDER)
    'Тип события.'
    order: OrderShortcut
    'Объект обнаруженного заказа.'


@dataclass(unsafe_hash=True)
class OrdersListChangedEvent(BaseEvent):
    '''
    Класс события: список заказов и/или статус одного/нескольких заказов изменился.

    :param runner_tag: Тег Runner'а.
    :type runner_tag: str
    :param purchases: Кол-во незавершенных покупок.
    :type purchases: int
    :param sales: Кол-во незавершенных продаж.
    :type sales: int
    '''
    type: EventTypes = field(init=False, default=EventTypes.ORDERS_LIST_CHANGED)
    'Тип события.'
    purchases: int
    'Кол-во незавершенных покупок.'
    sales: int
    'Кол-во незавершенных продаж.'


@dataclass(unsafe_hash=True)
class NewOrderEvent(BaseEvent):
    '''
    Класс события: в списке заказов обнаружен новый заказ.

    :param runner_tag: Тег Runner'а.
    :type runner_tag: str
    :param order: Объект нового заказа.
    :type order: OrderShortcut
    '''
    type: EventTypes = field(init=False, default=EventTypes.NEW_ORDER)
    'Тип события.'
    order: OrderShortcut
    'Объект нового заказа.'


@dataclass(unsafe_hash=True)
class OrderStatusChangedEvent(BaseEvent):
    '''
    Класс события: статус заказа изменился.

    :param runner_tag: Тег Runner'а.
    :type runner_tag: str
    :param order: Объект нового заказа.
    :type order: Объект измененного заказа.
    '''
    type: EventTypes = field(init=False, default=EventTypes.ORDER_STATUS_CHANGED)
    'Тип события.'
    order: OrderShortcut
    'Объект измененного заказа.'


# ----------------------------- Объекты Runner'а ----------------------------- #
@dataclass(unsafe_hash=True)
class RunnerPayload:
    '''
    Класс, описывающий полезную нагрузку, отправляемую в запросе runner/.

    :param objects: Список объектов, отправляемых в / получаемых из запроса, defaults to [].
    :type objects: list[RunnerObject], опционально
    :param request: Объект, описывающий запрос, defaults to False.
    :type request: RunnerRequest | False, опционально
    '''
    objects: list[RunnerObject] = field(default_factory=list)
    'Список объектов, отправляемых в / получаемых из запроса.'
    request: RunnerRequest | Literal[False] = False
    'Объект, описывающий запрос.'


    def to_json(self) -> dict[Literal['objects', 'request'], str]:
        return {
            'objects': json.dumps([obj.to_dict() for obj in self.objects]),
            'request': self.request if self.request is False else json.dumps(self.request.to_dict())
        }


@dataclass
class RunnerObject:
    '''
    Класс, описывающий объект запроса runner/.

    :param type: Тип объекта.
    :type type: str
    :param id: Айди аккаунта пользователя / пользователей.
    :type id: int | str
    :param tag: Тег запроса раннера, defaults to '00000000'.
    :type tag: str, опционально
    :param data: Информация об объекте, defaults to False.
    :type data: dict | False, опционально
    '''
    type: Literal['orders_counters', 'chat_bookmarks', 'c-p-u', 'chat_node'] | str
    'Тип объекта.'
    id: int | str
    'Айди пользователя / пользователей.'
    tag: str = '00000000'
    'Тег запроса раннера.'
    data: dict | Literal[False] = False
    'Информация об объекте.'


    def to_dict(self) -> dict[str, str]:
        return {
            'type': self.type,
            'id': self.id,
            'tag': self.tag,
            'data': self.data
        }


    @classmethod
    def from_json(cls, obj: dict) -> Self:
        return cls(
            obj['type'],
            obj['id'],
            obj['tag'],
            obj['data']
        )


    def __hash__(self): return hash((self.type, self.id, self.tag, tuple(self.data.values())))


@dataclass
class RunnerRequest:
    '''
    Класс, описывающий запрос runner/.

    :param action: Тип действия (запроса).
    :type action: str
    :param data: Информация о запросе, defaults to False.
    :type data: dict | False, опционально
    '''
    action: Literal['chat_message'] | str
    'Тип действия (запроса).'
    data: dict | Literal[False] = False
    'Информация о запросе.'


    def to_dict(self) -> dict[str, str]:
        return {
            'action': self.action,
            'data': self.data
        }


    def __hash__(self): return hash((self.action, tuple(self.data.values())))


@dataclass
class RunnerResponse:
    '''
    Класс, описывающий ответ запроса runner/.
    '''
    objects: list[RunnerObject] = field(default_factory=list)
    response: dict | Literal[False] = False

    @classmethod
    def from_json(cls, obj: dict) -> Self: return cls(
        objects=[] if not obj.get('objects') else [RunnerObject.from_json(object) for object in obj['objects']],
        response=obj.get('response', False)
    )


__all__ = [
    'BuyerViewing',
    'ChatShortcut',
    'Chat',
    'Message',
    'OrderShortcut',
    'Order',
    'Category',
    'SubCategory',
    'LotFields',
    'ChipOffer',
    'ChipFields',
    'LotPage',
    'SellerShortcut',
    'LotShortcut',
    'MyLotShortcut',
    'UserProfile',
    'Review',
    'Balance',
    'PaymentMethod',
    'CalcResult',
    'InitialChatEvent',
    'ChatsListChangedEvent',
    'LastChatMessageChangedEvent',
    'NewMessageEvent',
    'InitialOrderEvent',
    'OrdersListChangedEvent',
    'NewOrderEvent',
    'OrderStatusChangedEvent',
    'RunnerPayload',
    'RunnerObject',
    'RunnerRequest',
    'RunnerResponse'
]