from __future__ import annotations


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Runner


    from requests import Response


    from typing import ParamSpec, TypeVar


    F_Spec = ParamSpec('F_Spec')
    F_Return = TypeVar('F_Return')


from . import (
    exceptions, MessageTypes, OrderStatuses, SubCategoryTypes, Currencies, Wallets, Months, generate_random_tag, PRIVATE_CHAT_ID_RE, PRODUCTS_AMOUNT_RE, EXCHANGE_RATE_RE,
    FUNPAY_URL_RE, BuyerViewing, ChatShortcut, Chat, Message, OrderShortcut, Order, Category, SubCategory, LotFields, ChipFields, LotPage, SellerShortcut, LotShortcut,
    MyLotShortcut, UserProfile, Review, Balance, PaymentMethod, CalcResult, RunnerRequest, RunnerObject, RunnerPayload, RunnerResponse, FloodErrorTexts,
    MultiuserFloodErrorTexts
)


from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import JSONDecodeError
from requests_toolbelt import MultipartEncoder
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup, Tag


from pathlib import Path
from datetime import datetime, timedelta
from logging import getLogger
import random
import string
import json
from time import time, sleep
from typing import Literal, Any, Optional, IO, Callable
from functools import wraps


logger = getLogger('FunPayAPI.account')


# F_Spec = ParamSpec('F_Spec')
# F_Return = TypeVar('F_Return')


def _raise_if_acc_is_not_initiated(
        call: Callable[F_Spec, F_Return]
) -> Callable[F_Spec, F_Return]:
    '''
    Поднимает :class:`common.exceptions.AccountNotInitiatedError`, если класс не инициализирован.
    '''
    @wraps(call)
    def wrapper(*args: F_Spec.args, **kwargs: F_Spec.kwargs) -> F_Return:
        if not args[0].is_initiated: raise exceptions.AccountNotInitiatedError()


        return call(*args, **kwargs)


    return wrapper


class Account:
    def __init__(
            self, golden_key: str,
            user_agent: str | None = None,
            requests_timeout: int | float = 10,
            proxy: dict | None = None,
            locale: Literal['ru', 'en', 'uk'] | None = None
    ):
        '''
        Класс для управления аккаунтом FunPay.

        :param golden_key: Токен (golden_key) аккаунта.
        :type golden_key: :obj:`str`
        :param user_agent: User-agent браузера, с которого был произведен вход в аккаунт, defaults to :obj:`None`.
        :type user_agent: :obj:`str` | :obj:`None`, опционально
        :param requests_timeout: Тайм-аут ожидания ответа на запросы, defaults to :obj:`10`.
        :type requests_timeout: :obj:`int` | :obj:`float`, опционально
        :param proxy: Прокси для запросов, defaults to :obj:`None`.
        :type proxy: :obj:`dict` | :obj:`None`, опционально
        :param locale: Текущий язык аккаунта, defaults to :obj:`None`.
        :type locale: :obj:`Literal['ru', 'en', 'uk']` | :obj:`None`, опционально
        '''
        self.golden_key: str = golden_key
        'Токен (golden_key) аккаунта.'

        self.user_agent: str | None = user_agent
        'User-agent браузера, с которого был произведен вход в аккаунт.'


        self.requests_timeout: int | float = requests_timeout
        'Тайм-аут ожидания ответа на запросы.'

        self.proxy = proxy
        'Прокси для запросов к FunPay.'


        self.runner: Runner | None = None
        'Объект Runner\'а.'


        self.html: str | None = None
        'HTML основной страницы FunPay.'


        self.app_data: dict | None = None
        'Appdata.'

        self.csrf_token: str | None = None
        'CSRF токен.'

        self.id: int | None = None
        'Айди аккаунта.'

        self.username: str | None = None
        'Никнейм аккаунта.'


        self.phpsessid: str | None = None
        'PHPSESSID сессии.'


        self._logout_link: str | None = None
        'Ссылка для выхода с аккаунта.'


        self.active_sales: int | None = None
        'Активные продажи.'

        self.active_purchases: int | None = None
        'Активные покупки.'


        self.last_429_err_time: float = 0
        'Время последнего возникновения 429 ошибки.'

        self.last_flood_err_time: float = 0
        'Время последнего возникновения ошибки `"Нельзя отправлять сообщения слишком часто."`.'

        self.last_multiuser_flood_err_time: float = 0
        'Время последнего возникновения ошибки `"Нельзя слишком часто отправлять сообщения разным пользователям."`.'


        self.__locale: Literal['ru', 'en', 'uk'] | None = None
        'Текущий язык аккаунта.'

        self.__set_locale: Literal['ru', 'en', 'uk'] | None = None
        'Язык, на который будет переведен аккаунт при следующем GET-запросе.'

        self.__default_locale: Literal['ru', 'en', 'uk'] | None = locale
        'Язык аккаунта по умолчанию.'


        self.__profile_parse_locale: Literal['ru', 'en', 'uk'] | None = locale
        'Язык по умолчанию для :meth:`get_user`.'

        self.__chat_parse_locale: Literal['ru', 'en', 'uk'] | None = None
        'Язык по умолчанию для :meth:`get_chat`.'

        # self.__sales_parse_locale: Literal['ru', 'en', 'uk'] | None = locale #TODO
        'Язык по умолчанию для :meth:`get_sales`.'

        self.__order_parse_locale: Literal['ru', 'en', 'uk'] | None = None
        'Язык по умолчанию для :meth:`get_order`.'

        self.__lots_parse_locale: Literal['ru', 'en', 'uk'] | None = None
        'Язык по умолчанию для :meth:`get_subcategory_public_lots`.'

        self.__subcategories_parse_locale: Literal['ru', 'en', 'uk'] | None = None
        'Язык по умолчанию для получения названий разделов.'


        self.currency: Currencies = Currencies.UNKNOWN
        'Валюта аккаунта.'

        self.total_balance: int | None = None
        'Примерный общий баланс аккаунта в валюте аккаунта.'


        self.last_update: int | None = None
        'Последнее время обновления аккаунта.'


        self.__initiated: bool = False


        self.__saved_chats: dict[int, ChatShortcut] = {}


        self.__categories: list[Category] = []

        self.__sorted_categories: dict[int, Category] = {}

        self.__subcategories: list[SubCategory] = []

        self.__sorted_subcategories: dict[SubCategoryTypes, dict[int, SubCategory]] = {
            SubCategoryTypes.COMMON: {},
            SubCategoryTypes.CURRENCY: {}
        }


        self.__bot_character = '⁡'
        'Если сообщение начинается с этого символа, значит оно отправлено ботом.'


        self.session = Session()

        retry_strategy = Retry(
            total=6,
            connect=6,
            read=6,
            redirect=6,
            status=6,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods={'GET', 'POST'}
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)

        self.session.mount('https://', adapter)


    def method(
            self, request_method: Literal['post', 'get'], api_method: str,
            params: dict | None = None, headers: dict | None = None, payload: Any | None = None,
            exclude_phpsessid: bool = False, raise_not_200: bool = False,
            locale: Literal['ru', 'en', 'uk'] | None = None
    ) -> Response:
        '''
        Отправляет запрос к FunPay. Добавляет в заголовки запроса :obj:`user_agent` и куки.

        :param request_method: Метод запроса.
        :type request_method: :obj:`str`
        :param api_method: Метод API.
        :type api_method: :obj:`str`
        :param params: Параметры запроса, defaults to :obj:`None`.
        :type params: :obj:`dict` | None, опционально
        :param headers: Заголовки запроса, defaults to :obj:`None`.
        :type headers: :obj:`dict` | None, опционально
        :param payload: Полезная нагрузка запроса, defaults to :obj:`None`.
        :type payload: :obj:`Any` | None, опционально
        :param exclude_phpsessid: Исключить :obj:`phpsessid` из добавляемых куки, defaults to :obj:`False`.
        :type exclude_phpsessid: :obj:`bool`, опционально
        :param raise_not_200: Возбуждать исключение, если код ответа != 200, defaults to :obj:`False`.
        :type raise_not_200: :obj:`bool`, опционально
        :param locale: Язык аккаунта, defaults to :obj:`None`.
        :type locale: :obj:`str` | `None`, опционально
        :raises :class:`common.exceptions.UnauthorizedError`: Поднимается, если пользователь не авторизован.
        :raises :class:`common.exceptions.RequestFailedError`: Поднимается, если статус-код ответа != 200.
        :return: Объект ответа.
        :rtype: :class:`Response`
        '''
        def normalize_url(api_method: str, locale: Literal['ru', 'en', 'uk'] | None = None) -> str:
            api_method = 'https://funpay.com/' if api_method == 'https://funpay.com' else api_method
            url = api_method if api_method.startswith('https://funpay.com/') else 'https://funpay.com/' + api_method


            match = FUNPAY_URL_RE.fullmatch(url)


            loc = match.groupdict().get('locale')

            if not locale: locale = self.locale
            locale = None if locale == 'ru' else locale

            if locale != loc: url = url.replace(
                f'https://funpay.com/{f'{loc}/' if loc else ''}',
                f'https://funpay.com/{f'{locale}/' if locale else ''}',
                1
            )


            return url


        def update_locale(redirect_url: str):
            for locale in ('en', 'uk'):
                if redirect_url.startswith(f'https://funpay.com/{locale}/'):
                    self.__locale = locale
                    return

            if redirect_url.startswith(f'https://funpay.com'): self.__locale = 'ru'


        headers = headers or {}

        headers['cookie'] = f'golden_key={self.golden_key}; cookie_prefs=1'
        headers['cookie'] += f'; PHPSESSID={self.phpsessid}' if self.phpsessid and not exclude_phpsessid else ''

        if self.user_agent: headers['user-agent'] = self.user_agent


        if request_method == 'post' and locale: link = normalize_url(api_method, locale)

        else: link = normalize_url(api_method)


        params = params or {}


        if request_method == 'get' and locale and locale != self.locale: params['setlocale'] = locale


        locale = locale or self.__set_locale


        kwargs = {
            'method': request_method,
            'data': payload or {},
            'headers': headers,
            'timeout': self.requests_timeout,
            'proxies': self.proxy or {}
        }


        logger.debug(f'Отправляю запрос {request_method.upper()} к {link}.')

        _ = 0
        response = None

        while _ < 10 or response.status_code == 429:
            _ += 1

            response = self.session.request(
                url=link,
                params=params if _ <= 1 else {},
                allow_redirects=False,
                **kwargs
            )

            if response.status_code == 429:
                self.last_429_err_time = time()
                sleep(min(2 ** _, 30))


                continue

            elif not (300 <= response.status_code < 400) or 'Location' not in response.headers: break


            link = response.headers['Location']
            update_locale(link)

            if _ < 10: logger.debug(f'Редирект к {link} ({_}).')

        else: response = self.session.request(
            url=link,
            allow_redirects=True,
            **kwargs
        )


        if response.status_code == 403: raise exceptions.UnauthorizedError(response)

        elif response.status_code != 200 and raise_not_200: raise exceptions.RequestFailedError(response)


        return response


    def get(self, update_phpsessid: bool = True) -> Account:
        '''
        Получает / обновляет данные об аккаунте. Необходимо вызывать каждые 40-60 минут, дабы обновить :obj:`phpsessid`.

        :param update_phpsessid: Обновить :obj:`phpsessid`, defaults to :obj:`True`
        :type update_phpsessid: :obj:`bool`, опционально
        :raises :class:`common.exceptions.UnauthorizedError`: Поднимается, если пользователь не авторизован.
        :return: Объект аккаунта с обновленными данными.
        :rtype: :class:`Account`
        '''
        logger.info(f'Получаю данные об аккаунте.')

        response = self.method('get', 'https://funpay.com/', exclude_phpsessid=update_phpsessid, raise_not_200=True, locale=self.__subcategories_parse_locale)


        if not self.is_initiated: self.locale = self.__default_locale


        html_response = response.content.decode()

        parser = BeautifulSoup(html_response, 'lxml')

        username = parser.find('div', {'class': 'user-link-name'})

        if not username: raise exceptions.UnauthorizedError(response)


        self.username = username.text


        self.__update_app_data(parser, get_user_id=True, get_locale=True, get_csrf_token=True)


        self._logout_link = parser.find('a', {'class': 'menu-item-logout'}).get('href')


        active_sales = parser.find('span', {'class': 'badge badge-trade'})

        self.active_sales = int(active_sales.text) if active_sales else 0


        balance = parser.find('span', {'class': 'badge badge-balance'})

        if balance:
            balance, currency = balance.text.rsplit(' ', maxsplit=1)

            self.total_balance = int(balance.replace(' ', ''))
            self.currency = Currencies(currency)

        else: self.total_balance = 0


        active_purchases = parser.find('span', {'class': 'badge badge-orders'})

        self.active_purchases = int(active_purchases.text) if active_purchases else 0


        cookies = response.cookies.get_dict()

        if update_phpsessid or not self.phpsessid: self.phpsessid = cookies.get('PHPSESSID', self.phpsessid)


        if not self.is_initiated: self.__setup_categories(html_response)


        self.last_update = int(time())

        self.html = html_response

        self.__initiated = True


        return self


    @_raise_if_acc_is_not_initiated
    def get_subcategory_public_lots(self, subcategory_type: SubCategoryTypes, subcategory_id: int, locale: Literal['ru', 'en', 'uk'] | None = None) -> list[LotShortcut]:
        '''
        Получает список всех опубликованных лотов переданной подкатегории.

        :param subcategory_type: Тип подкатегории.
        :type subcategory_type: :class:`SubCategoryTypes`
        :param subcategory_id: Айди подкатегории.
        :type subcategory_id: :obj:`int`
        :param locale: Язык аккаунта, который будет установлен при запросе к FunPay, defaults to :obj:`None`.
        :type locale: :obj:`Literal['ru', 'en', 'uk']` | :obj:`None`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.UnauthorizedError`: Поднимается, если пользователь не авторизован.
        :return: Список всех опубликованных лотов переданной подкатегории.
        :rtype: :obj:`list[LotShortcut]`
        '''
        logger.debug(f'Получаю список лотов подкатегории {subcategory_id}.')

        url = f'https://funpay.com/{'lots' if subcategory_type is SubCategoryTypes.COMMON else 'chips'}/{subcategory_id}/'

        headers = {'accept': '*/*'}

        if not locale: locale = self.__lots_parse_locale

        response = self.method('get', url, headers=headers, raise_not_200=True, locale=locale)


        if locale: self.locale = self.__default_locale


        html_response = response.content.decode()

        parser = BeautifulSoup(html_response, 'lxml')


        username = parser.find('div', {'class': 'user-link-name'})

        if not username: raise exceptions.UnauthorizedError(response)


        self.__update_app_data(parser)


        offers = parser.find_all('a', {'class': 'tc-item'})

        if not offers: return []


        subcategory_obj = self.get_subcategory(subcategory_type, subcategory_id)


        result = self.__parse_lot_shortcuts(offers, subcategory_obj, True)


        if result:
            if result[0].currency != self.currency: self.currency = result[0].currency


        return result


    @_raise_if_acc_is_not_initiated
    def get_my_subcategory_lots(self, subcategory_id: int, locale: Literal['ru', 'en', 'uk'] | None = None) -> list[MyLotShortcut]:
        '''
        Получает лоты со страницы https://funpay.com/lots/{айди_подкатегории}/trade.

        :param subcategory_id: Айди подкатегории.
        :type subcategory_id: :obj:`int`
        :param locale: Язык аккаунта, который будет установлен при запросе к FunPay, defaults to :obj:`None`.
        :type locale: :obj:`Literal['ru', 'en', 'uk']` | :obj:`None`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.UnauthorizedError`: Поднимается, если пользователь не авторизован.
        :return: Список лотов переданной подкатегории на аккаунте.
        :rtype: :obj:`list[MyLotShortcut]`
        '''
        url = f'https://funpay.com/lots/{subcategory_id}/trade'

        headers = {'accept': '*/*'}

        if not locale: locale = self.__lots_parse_locale

        response = self.method('get', url, headers=headers, raise_not_200=True, locale=locale)


        if locale: self.locale = self.__default_locale


        html_response = response.content.decode()

        parser = BeautifulSoup(html_response, 'lxml')


        username = parser.find('div', {'class': 'user-link-name'})

        if not username: raise exceptions.UnauthorizedError(response)


        self.__update_app_data(parser)


        offers = parser.find_all('a', class_='tc-item')

        if not offers: return []


        subcategory_obj = self.get_subcategory(SubCategoryTypes.COMMON, subcategory_id)


        result = self.__parse_lot_shortcuts(offers, subcategory_obj, my_lots=True)


        if result:
            if self.currency != result[0].currency: self.currency = result[0].currency


        return result


    @_raise_if_acc_is_not_initiated
    def get_lot_page(self, lot_id: int, locale: Literal['ru', 'en', 'uk'] | None = None) -> LotPage | None:
        '''
        Возвращает страницу лота.

        :param lot_id: Айди лота.
        :type lot_id: :obj:`int`
        :param locale: Язык аккаунта, который будет установлен при запросе к FunPay, defaults to :obj:`None`.
        :type locale: :obj:`Literal['ru', 'en', 'uk']` | :obj:`None`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.UnauthorizedError`: Поднимается, если пользователь не авторизован.
        :return: Объект страницы лота или :obj:`None`, если лот не найден.
        :rtype: :class:`LotPage` | :obj:`None`
        '''
        logger.debug(f'Получаю страницу лота {lot_id}')

        url = f'https://funpay.com/lots/offer?id={lot_id}'

        headers = {'accept': '*/*'}

        response = self.method('get', url, headers=headers, raise_not_200=True, locale=locale)


        if locale: self.locale = self.__default_locale


        html_response = response.content.decode()

        parser = BeautifulSoup(html_response, 'lxml')


        username = parser.find('div', {'class': 'user-link-name'})

        if not username: raise exceptions.UnauthorizedError(response)


        self.__update_app_data(parser)


        if (
            (page_header := parser.find('h1', {'class': 'page-header'})) and
            (page_header.text in ('Предложение не найдено', 'Пропозицію не знайдено', 'Offer not found'))
        ): return None


        subcategory_id = int(parser.find('a', {'class': 'js-back-link'})['href'].split('/')[-2])

        subcategory_obj = self.get_subcategory(SubCategoryTypes.COMMON, subcategory_id)


        chat_header = parser.find('div', {'class': 'chat-header'})

        if chat_header:
            seller = chat_header.find('div', {'class': 'media-user-name'}).find('a')

            seller_id = int(seller['href'].split('/')[-2])

            seller_username = seller.text

        else:
            seller_id = self.id

            seller_username = self.username


        short_description = None

        detailed_description = None

        image_urls = []

        for param_item in parser.find_all('div', {'class': 'param-item'}):
            if param_name := param_item.find('h5'):
                if param_name.text in ('Краткое описание', 'Короткий опис', 'Short description'): short_description = param_item.find('div').text

                elif param_name.text in ('Подробное описание', 'Докладний опис', 'Detailed description'): detailed_description = param_item.find('div').text

                elif param_name in ('Картинки', 'Зображення', 'Images'):
                    photos = param_item.find_all('a', {'class': 'attachments-thumb'})

                    if photos: image_urls = [photo.get('href') for photo in photos]


        return LotPage(
            lot_id,
            subcategory_obj,
            short_description,
            detailed_description,
            image_urls,
            seller_id,
            seller_username
        )


    @_raise_if_acc_is_not_initiated
    def get_balance(self, lot_id: int, locale: Literal['ru', 'en', 'uk'] | None = None) -> Balance:
        '''
        Получает информацию о балансе пользователя.

        :param lot_id: Айди лота, на котором проверять баланс.
        :type lot_id: :obj:`int`
        :param locale: Язык аккаунта, который будет установлен при запросе к FunPay, defaults to :obj:`None`.
        :type locale: :obj:`Literal['ru', 'en', 'uk']` | :obj:`None`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.UnauthorizedError`: Поднимается, если пользователь не авторизован.
        :return: Объект баланса пользователя.
        :rtype: :class:`Balance`
        '''
        logger.debug(f'Получаю баланс (lot_id={lot_id}).')

        url = f'https://funpay.com/lots/offer?id={lot_id}'

        headers = {'accept': '*/*'}

        response = self.method('get', url, headers=headers, raise_not_200=True, locale=locale)


        if locale: self.locale = self.__default_locale


        html_response = response.content.decode()

        parser = BeautifulSoup(html_response, 'lxml')


        username = parser.find('div', {'class': 'user-link-name'})

        if not username: raise exceptions.UnauthorizedError(response)


        self.__update_app_data(parser)


        balances = parser.find('select', {'name': 'method'})

        balance = Balance(
            float(balances['data-balance-total-rub']),
            float(balances['data-balance-rub']),
            float(balances['data-balance-total-usd']),
            float(balances['data-balance-usd']),
            float(balances['data-balance-total-eur']),
            float(balances['data-balance-eur'])
        )


        return balance


    @_raise_if_acc_is_not_initiated
    def get_chat_history(
        self, chat_id: int | str,
        last_message_id: int = 99999999999999999999999, interlocutor_username: str | None = None, from_id: int = 0,
        locale: Literal['ru', 'en', 'uk'] | None = None
    ) -> list[Message]:
        '''
        Получает историю указанного чата (до 100 последних сообщений).

        :param chat_id: Айди чата.
        :type chat_id: :obj:`int` | :obj:`str`
        :param last_message_id: Айди сообщения, с которого начинать историю, defaults to :obj:`99999999999999999999999`.
        :type last_message_id: :obj:`int`, опционально
        :param interlocutor_username: Никнейм собеседника. Не нужно указывать для получения истории публичного чата, defaults to :obj:`None`.
        Также необязательно, но желательно указывать для получения истории личного чата.
        :type interlocutor_username: :obj:`str` | :obj:`None`, опционально
        :param from_id: Все сообщения с айди < переданного не попадут в возвращаемый список сообщений, defaults to :obj:`0`.
        :type from_id: :obj:`int`, опционально
        :param locale: Язык аккаунта, который будет установлен при запросе к FunPay, defaults to :obj:`None`.
        :type locale: :obj:`Literal['ru', 'en', 'uk']` | :obj:`None`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :return: История указанного чата.
        :rtype: :obj:`list[Message]`
        '''
        logger.debug(f'Получаю историю чата {interlocutor_username or chat_id}{f' ({chat_id})' if interlocutor_username else ''}.')

        url = f'https://funpay.com/chat/history'

        params = {'node': chat_id, 'last_message': last_message_id}

        headers = {'accept': '*/*', 'x-requested-with': 'XMLHttpRequest'}

        payload = {'node': chat_id, 'last_message': last_message_id}

        response = self.method('get', url, params=params, headers=headers, payload=payload, raise_not_200=True, locale=locale)


        json_response = response.json()

        if not json_response.get('chat') or not json_response['chat'].get('messages'): return []


        if json_response['chat']['node']['silent']: interlocutor_id = None

        else:
            interlocutors = json_response['chat']['node']['name'].split('-')[1:]

            interlocutors.remove(str(self.id))

            interlocutor_id = int(interlocutors[0])


        return self.__parse_messages(json_response['chat']['messages'], chat_id, interlocutor_id, interlocutor_username, from_id)


    @_raise_if_acc_is_not_initiated
    def get_chats_histories(self, chats_data: dict[int | str, str | None]) -> dict[int, list[Message]]:
        '''
        Получает историю сообщений сразу нескольких чатов (до 50 сообщений на личный чат, до 25 сообщений на публичный чат).

        :param chats_data: Айди чатов и никнеймы собеседников (None, если никнейм неизвестен).
        Например: {48392847: 'SLLMK', 58392098: 'Amongus', 38948728: None}
        :type chats_data: :obj:`dict[int  |  str, str  |  None]`
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :return: Словарь с историями чатов в формате {Айди чата: [список сообщений]}.
        :rtype: :obj:`dict[int, list[Message]]`
        '''
        logger.debug(f'Получаю историю чатов {chats_data}.')

        chats = [
            RunnerObject(
                'chat_node',
                chat_id,
                data={'node': chat_id, 'last_message': -1, 'content': ''}
            ) for chat_id in chats_data
        ]

        payload = RunnerPayload(
            chats
        )

        response = self.runner.send_request(payload)

        response_obj = RunnerResponse.from_json(response.json())

        logger.debug(f'Получен ответ: {response_obj}')


        result = {}

        for obj in response_obj.objects:
            if obj.type == 'chat_node':
                if not obj.data:
                    result[obj.id] = []
                    continue


                if obj.data['node']['silent']:
                    interlocutor_id = None
                    interlocutor_name = None

                else:
                    interlocutors = obj.data['node']['name'].split('-')[1:]
                    interlocutors.remove(str(self.id))

                    interlocutor_id = int(interlocutors[0])

                    interlocutor_name = chats_data[obj.id]


                messages = self.__parse_messages(obj.data['messages'], obj.id, interlocutor_id, interlocutor_name)

                result[obj.id] = messages


        return result


    @_raise_if_acc_is_not_initiated
    def upload_image(self, image: str | Path | IO[bytes], image_type: Literal['chat', 'offer'] = 'chat') -> int:
        '''
        Выгружает изображение на сервер FunPay для дальнейшей отправки в качестве сообщения.

        Для отправки изображения в чат рекомендуется использовать метод :meth:`send_image`.

        :param image: Путь до изображения или представление изображения в виде байтов.
        :type image: :obj:`str` | :class:`Path` | :obj:`bytes`
        :param image_type: Тип изображения (куда загружать), defaults to :obj:`'chat'`.
        :type image_type: :obj:`Literal['chat', 'offer']`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.ImageUploadError`: Поднимается, если статус-код ответа = 400 или в ответе нет айди изображения.
        :raises :class:`common.exceptions.RequestFailedError`: Поднимается во всех остальных случаях.
        :return: Айди изображения на серверах FunPay.
        :rtype: :obj:`int`
        '''
        logger.debug(f'Выгружаю изображение {image}.')

        image = Path(image).read_bytes() if isinstance(image, str) else image.read_bytes() if isinstance(image, Path) else image


        url = f'https://funpay.com/file/add{image_type.title()}Image'

        fields = {
            'file': ('Sent_by_crd_ext.png', image, 'image/png'),
            'file_id': '0'
        }

        boundary = '----WebKitFormBoundary' + ''.join(random.sample(string.ascii_letters + string.digits, 16))

        encoder = MultipartEncoder(fields=fields, boundary=boundary)

        headers = {'accept': '*/*', 'x-requested-with': 'XMLHttpRequest', 'content-type': encoder.content_type}

        response = self.method('post', url, headers=headers, payload=encoder)


        if response.status_code == 400:
            try:
                json_response = response.json()
                message = json_response.get('msg')

                raise exceptions.ImageUploadError(response, message)

            except JSONDecodeError: raise exceptions.ImageUploadError(response, None)

        elif response.status_code != 200: raise exceptions.RequestFailedError(response)

        if not (document_id := response.json().get('fileId')): raise exceptions.ImageUploadError(response, None)


        return int(document_id)


    @_raise_if_acc_is_not_initiated
    def send_message(
        self, chat_id: int | str, text: str | None = None, chat_name: str | None = None,
        interlocutor_id: int | None = None,
        image_id: int | None = None,
        add_to_ignore_list: bool = True, update_last_saved_message: bool = False, leave_as_unread: bool = False
    ) -> Message:
        '''
        Отправляет сообщение в чат.

        :param chat_id: Айди чата.
        :type chat_id: :obj:`int` | :obj:`str`
        :param text: Текст сообщения, defaults to :obj:`None`.
        :type text: :obj:`str` | :obj:`None`, опционально
        :param chat_name: Название чата (для возвращаемого объекта сообщения) (не нужно для отправки сообщения в публичный чат), defaults to :obj:`None`.
        :type chat_name: :obj:`str` | :obj:`None`, опционально
        :param interlocutor_id: Айди собеседника (не нужно для отправки сообщения в публичный чат), defaults to :obj:`None`.
        :type interlocutor_id: :obj:`int` | :obj:`None`, опционально
        :param image_id: Айди изображения. Доступно только для личных чатов, defaults to :obj:`None`.
        :type image_id: :obj:`int` | :obj:`None`, опционально
        :param add_to_ignore_list: Добавлять ли айди отправленного сообщения в игнорируемый список Runner'а, defaults to :obj:`True`.
        :type add_to_ignore_list: :obj:`bool`, опционально
        :param update_last_saved_message: Обновлять ли последнее сохраненное сообщение на отправленное в Runner'е, defaults to :obj:`False`.
        :type update_last_saved_message: :obj:`bool`, опционально
        :param leave_as_unread: Оставлять ли сообщение непрочитанным при отправке, defaults to :obj:`False`.
        :type leave_as_unread: :obj:`bool`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.MessageNotDeliveredError`: Поднимается, если не удалось отправить сообщение.
        :return: Отправленное сообщение.
        :rtype: :class:`Message`
        '''
        logger.debug(f'Отправляю сообщение в чат {chat_id}.')
        logger.debug(f'Image: {image_id}' if image_id else text)

        request = RunnerRequest(
            'chat_message',
            {'node': chat_id, 'last_message': -1}
        )

        if image_id is not None:
            request.data['image_id'] = image_id
            request.data['content'] = ''

        else: request.data['content'] = f'{self.__bot_character}{text}' if text else ''

        chats_data = RunnerObject(
            'chat_node',
            chat_id,
            data={'node': chat_id, 'last_message': -1, 'content': ''}
        )

        payload = RunnerPayload(
            [chats_data],
            request
        )

        response = self.runner.send_request(payload)

        response_obj = RunnerResponse.from_json(response.json())

        logger.debug(f'Получен ответ: {response_obj}')


        if not response_obj.response: raise exceptions.MessageNotDeliveredError(response, None, chat_id)


        if (error := response_obj.response.get('error')) is not None:
            if error in [error_text.value for error_text in FloodErrorTexts]: self.last_flood_err_time = time()
            elif error in [error_text.value for error_text in MultiuserFloodErrorTexts]: self.last_multiuser_flood_err_time = time()

            raise exceptions.MessageNotDeliveredError(response, error, chat_id)


        if leave_as_unread:
            msg_id = 0

            msg_text = text

            msg_html = f'''
            <div class="chat-msg-item" id="message-0000000000">
                <div class="chat-message">
                    <div class="chat-msg-body">
                        <div class="chat-msg-text">{msg_text}</div>
                    </div>
                </div>
            </div>
            '''

            image_name = None
            image_link = None

        else:
            msg = response_obj.objects[0].data['messages'][-1]

            parser = BeautifulSoup(msg['html'].replace('<br>', '\n'), 'lxml')

            msg_id = msg['id']

            try:
                if image_tag:=parser.find('a', {'class': 'chat-img-link'}):
                    msg_text = None

                    image_name = image_tag.find('img')
                    image_name = image_name.get('alt') if image_name else None
                    image_link = image_tag.get('href')

                else:
                    msg_text = parser.find('div', {'class': 'chat-msg-text'}).text.replace(self.__bot_character, '', 1)

                    image_name = None
                    image_link = None

            except Exception as e:
                logger.debug('SEND_MESSAGE RESPONSE')
                logger.debug(response.content.decode())
                raise e


            msg_html = msg['html']


        message_obj = Message(
            msg_id,
            msg_text,
            chat_id,
            chat_name,
            interlocutor_id,
            self.username,
            self.id,
            msg_html,
            by_bot=True,
            image_link=image_link,
            image_name=image_name
        )


        if self.runner and isinstance(chat_id, int):
            if add_to_ignore_list and message_obj.id: self.runner.mark_as_by_bot(chat_id, message_obj.id)

            if update_last_saved_message: self.runner.update_chat_last_message(chat_id, message_obj.id, message_obj.text)


        return message_obj


    @_raise_if_acc_is_not_initiated
    def send_image(
        self, chat_id: int, image: int | str | Path | IO[bytes], chat_name: str | None = None,
        interlocutor_id: int | None = None,
        add_to_ignore_list: bool = True, update_last_saved_message: bool = False, leave_as_unread: bool = False
    ) -> Message:
        '''
        Отправляет изображение в чат. Доступно только для личных чатов.

        :param chat_id: Айди чата.
        :type chat_id: :obj:`int`
        :param image: Айди изображения / путь до изображения / изображение в виде байтов.
        :type image: :obj:`int` | :obj:`str` | :obj:`Path` | :obj:`bytes`
        :param chat_name: Название чата (никнейм собеседника). Нужен для возвращаемого объекта, defaults to :obj:`None`
        :type chat_name: :obj:`str` | :obj:`None`, опционально
        :param interlocutor_id: Айди собеседника (не нужно для отправки сообщения в публичный чат), defaults to :obj:`None`
        :type interlocutor_id: :obj:`int` | :obj:`None`, опционально
        :param add_to_ignore_list: Добавлять ли айди отправленного сообщения в игнорируемый список Runner'а, defaults to :obj:`True`
        :type add_to_ignore_list: :obj:`bool`, опционально
        :param update_last_saved_message: Обновлять ли последнее сохраненное сообщение на отправленное в Runner'е, defaults to :obj:`False`
        :type update_last_saved_message: :obj:`bool`, опционально
        :param leave_as_unread: Оставлять ли сообщение непрочитанным при отправке, defaults to :obj:`False`
        :type leave_as_unread: :obj:`bool`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.MessageNotDeliveredError`: Поднимается, если не удалось отправить сообщение.
        :return: Объект отправленного сообщения
        :rtype: :class:`Message`
        '''
        if not isinstance(image, int): image = self.upload_image(image, image_type='chat')

        result = self.send_message(chat_id, None, chat_name, interlocutor_id, image, add_to_ignore_list, update_last_saved_message, leave_as_unread)


        return result


    @_raise_if_acc_is_not_initiated
    def send_review(self, order_id: str, text: str, rating: Literal[1, 2, 3, 4, 5] = 5) -> str:
        '''
        Отправляет / редактирует отзыв / ответ на отзыв.

        :param order_id: Айди заказа.
        :type order_id: :obj:`str`
        :param text: Текст отзыва.
        :type text: :obj:`str`
        :param rating: Рейтинг (от 1 до 5), defaults to :obj:`5`
        :type rating: :obj:`int`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.FeedbackEditingError`: Поднимается, если не удалось добавить/редактировать отзыв/ответ на отзыв.
        :raises :class:`common.exceptions.RequestFailedError`:  Поднимается, если статус-код ответа != 200.
        :return: Ответ FunPay (HTML-код блока отзыва).
        :rtype: :obj:`str`
        '''
        url = f'https://funpay.com/orders/review'

        headers = {'accept': '*/*', 'x-requested-with': 'XMLHttpRequest'}

        text = text.strip()

        payload = {
            'authorId': self.id,
            'text': f'{text}{self.__bot_character}' if text else text,
            'rating': rating,
            'csrf_token': self.csrf_token,
            'orderId': order_id
        }

        response = self.method('post', url, headers=headers, payload=payload)


        if response.status_code == 400:
            json_response = response.json()

            msg = json_response.get('msg')

            raise exceptions.FeedbackEditingError(response, msg, order_id)

        elif response.status_code != 200: raise exceptions.RequestFailedError(response)


        return response.json().get('content')


    @_raise_if_acc_is_not_initiated
    def delete_review(self, order_id: str) -> str:
        '''
        Удаляет отзыв / ответ на отзыв.

        :param order_id: Айди заказа.
        :type order_id: :obj:`str`
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.FeedbackEditingError`: Поднимается, если не удалось удалить отзыв/ответ на отзыв.
        :raises :class:`common.exceptions.RequestFailedError`:  Поднимается, если статус-код ответа != 200.
        :return: Ответ FunPay (HTML-код блока отзыва).
        :rtype: :obj:`str`
        '''
        url = f'https://funpay.com/orders/reviewDelete'

        headers = {'accept': '*/*', 'x-requested-with': 'XMLHttpRequest'}

        payload = {
            'authorId': self.id,
            'csrf_token': self.csrf_token,
            'orderId': order_id
        }

        response = self.method('post', url, headers=headers, payload=payload)


        if response.status_code == 400:
            json_response = response.json()

            msg = json_response.get('msg')

            raise exceptions.FeedbackEditingError(response, msg, order_id)

        elif response.status_code != 200: raise exceptions.RequestFailedError(response)


        return response.json().get('content')


    @_raise_if_acc_is_not_initiated
    def refund(self, order_id: str) -> None:
        '''
        Оформляет возврат средств за заказ.

        :param order_id: Айди заказа.
        :type order_id: :obj:`str`
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.RefundError`: Поднимается, если при возврате средств возникла ошибка.
        '''
        url = f'https://funpay.com/orders/refund'

        headers = {'accept': '*/*', 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8', 'x-requested-with': 'XMLHttpRequest'}

        payload = {
            'id': order_id,
            'csrf_token': self.csrf_token
        }

        response = self.method('post', url, headers=headers, payload=payload, raise_not_200=True)


        if response.json().get('error'): raise exceptions.RefundError(response, response.json().get('msg'), order_id)


    @_raise_if_acc_is_not_initiated
    def withdraw(self, currency: Currencies, wallet: Wallets, amount: int | float, address: str) -> float:
        '''
        Отправляет запрос на вывод средств.

        :param currency: Валюта.
        :type currency: :class:`Currencies`
        :param wallet: Тип кошелька.
        :type wallet: :class:`Wallets`
        :param amount: Кол-во средств.
        :type amount: :obj:`int` | :obj:`float`
        :param address: Адрес кошелька.
        :type address: :obj:`str`
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.WithdrawError`: Поднимается, если при выводе средств с аккаунта возникла ошибка.
        :return: Кол-во выведенных средств с учетом комиссии FunPay.
        :rtype: :obj:`float`
        '''
        url = f'https://funpay.com/withdraw/withdraw'

        wallets = {
            Wallets.QIWI: 'qiwi',
            Wallets.YOUMONEY: 'fps',
            Wallets.BINANCE: 'binance',
            Wallets.TRC: 'usdt_trc',
            Wallets.CARD_RUB: 'card_rub',
            Wallets.CARD_USD: 'card_usd',
            Wallets.CARD_EUR: 'card_eur',
            Wallets.WEBMONEY: 'wmz'
        }

        headers = {'accept': '*/*', 'x-requested-with': 'XMLHttpRequest'}

        payload = {
            'csrf_token': self.csrf_token,
            'currency_id': currency.name.lower(),
            'ext_currency_id': wallets[wallet],
            'wallet': address,
            'amount_int': str(amount)
        }

        response = self.method('post', url, headers=headers, payload=payload, raise_not_200=True)


        json_response = response.json()

        if json_response.get('error'):
            error_message = json_response.get('msg')

            raise exceptions.WithdrawError(response, error_message)


        return float(json_response.get('amount_ext'))


    @_raise_if_acc_is_not_initiated
    def get_raise_modal(self, category_id: int) -> dict:
        '''
        Отправляет запрос на получение modal-формы для поднятия лотов категории (игры).

        !ВНИМАНИЕ! Если на аккаунте только 1 подкатегория, относящаяся переданной категории (игре),
        то FunPay поднимет лоты данной подкатегории без отправления modal-формы с выбором других подкатегорий.

        :param category_id: Айди категории (игры).
        :type category_id: :obj:`int`
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :return: Ответ FunPay.
        :rtype: :obj:`dict`
        '''
        url = f'https://funpay.com/lots/raise'

        category = self.get_category(category_id)

        subcategory = category.subcategories[0]

        headers = {'accept': '*/*', 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8', 'x-requested-with': 'XMLHttpRequest'}

        payload = {
            'game_id': category_id,
            'node_id': subcategory.id
        }

        response = self.method('post', url, headers=headers, payload=payload, raise_not_200=True)

        json_response = response.json()


        return json_response


    @_raise_if_acc_is_not_initiated
    def raise_lots(self, category_id: int, subcategories: list[int | SubCategory] | None = None, exclude: list[int] | None = None) -> None:
        '''
        Поднимает все лоты всех подкатегорий переданной категории (игры).

        :param category_id: Айди категории (игры).
        :type category_id: :obj:`int`
        :param subcategories: Список подкатегорий, которые необходимо поднять. Если не указан, поднимутся все подкатегории переданной категории, defaults to None.
        :type subcategories: :obj:`list[int  |  SubCategory]` | :obj:`None`, опционально
        :param exclude: Айди подкатегорий, которые не нужно поднимать, defaults to None
        :type exclude: :obj:`list[int]` | :obj:`None`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises Exception: Поднимается, если не удалось найти указанную категорию (игру).
        :raises :class:`common.exceptions.RaiseError`: Поднимается, если не удалось поднять лоты.
        '''
        def __parse_wait_time(response: str) -> int:
            '''
            Парсит ответ FunPay на запрос о поднятии лотов.

            :param response: текст ответа.
            :return: Примерное время ожидание до следующего поднятия лотов (в секундах).
            '''
            x = ''.join([i for i in response if i.isdigit()])

            if 'секунд' in response or 'second' in response: return int(x) if x else 2

            elif 'минут' in response or 'хвилин' in response or 'minute' in response: return (int(x) - 1 if x else 1) * 60

            elif 'час' in response or 'годин' in response or 'hour' in response: return int((int(x) - 0.5 if x else 1) * 3600)

            else: return 10


        if not (category := self.get_category(category_id)): raise Exception('Not Found')  # TODO


        exclude = exclude or []

        if subcategories:
            subcats = []

            for i in subcategories:
                if isinstance(i, SubCategory):
                    if i.type is SubCategoryTypes.COMMON and i.category.id == category.id and i.id not in exclude: subcats.append(i)

                else:
                    if not (subcat := category.get_subcategory(SubCategoryTypes.COMMON, i)): continue

                    subcats.append(subcat)

        else: subcats = [i for i in category.subcategories if i.type is SubCategoryTypes.COMMON and i.id not in exclude]


        url = f'https://funpay.com/lots/raise'

        headers = {'accept': '*/*', 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8', 'x-requested-with': 'XMLHttpRequest'}

        payload = {
            'game_id': category_id,
            'node_id': subcats[0].id,
            'node_ids[]': [i.id for i in subcats]
        }

        response = self.method('post', url, headers=headers, payload=payload, raise_not_200=True)


        json_response = response.json()

        logger.debug(f'Ответ FunPay (поднятие категорий): {json_response}.')


        if not json_response.get('error') and not json_response.get('url'): return


        elif json_response.get('url'): raise exceptions.RaiseError(response, category, json_response.get('url'), 7200)

        elif json_response.get('error') and json_response.get('msg') and any([i in json_response.get('msg') for i in ('Подождите ', 'Please wait ', 'Зачекайте ')]):
            wait_time = __parse_wait_time(json_response.get('msg'))

            raise exceptions.RaiseError(response, category, json_response.get('msg'), wait_time)

        else: raise exceptions.RaiseError(response, category, json_response.get('msg'), None)


    @_raise_if_acc_is_not_initiated
    def get_user(self, user_id: int, locale: Literal['ru', 'en', 'uk'] | None = None) -> UserProfile:
        '''
        Парсит страницу пользователя.

        :param user_id: Айди пользователя.
        :type user_id: :obj:`int`
        :param locale: Язык аккаунта, который будет установлен при запросе к FunPay, defaults to None.
        :type locale: :obj:`Literal['ru', 'en', 'uk']` | :obj:`None`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :return: Объект профиля пользователя.
        :rtype: :class:`UserProfile`
        '''
        url = f'users/{user_id}/'

        headers = {'accept': '*/*'}

        if not locale: locale = self.__profile_parse_locale

        response = self.method('get', url, headers=headers, raise_not_200=True, locale=locale)


        if locale:  self.locale = self.__default_locale


        html_response = response.content.decode()

        parser = BeautifulSoup(html_response, 'lxml')


        username = parser.find('div', {'class': 'user-link-name'})

        if not username: raise exceptions.UnauthorizedError(response)


        self.__update_app_data(parser)


        username = parser.find('span', {'class': 'mr4'}).text


        user_status = parser.find('span', {'class': 'media-user-status'})

        user_status = user_status.text if user_status else ''


        avatar_link = parser.find('div', {'class': 'avatar-photo'}).get('style').split('(')[1].split(')')[0]

        avatar_link = avatar_link if avatar_link.startswith('https') else f'https://funpay.com{avatar_link}'


        banned = bool(parser.find('span', {'class': 'label label-danger'}))


        user_obj = UserProfile(
            user_id,
            username,
            avatar_link,
            'Онлайн' in user_status or 'Online' in user_status,
            banned,
            html_response
        )


        subcategory_divs = parser.find_all('div', {'class': 'offer-list-title-container'})

        if not subcategory_divs: return user_obj


        for subcategory_div in subcategory_divs:
            subcategory_link = subcategory_div.find('h3').find('a').get('href')

            subcategory_id = int(subcategory_link.split('/')[-2])

            subcategory_type = SubCategoryTypes.CURRENCY if 'chips' in subcategory_link else SubCategoryTypes.COMMON


            subcategory_obj = self.get_subcategory(subcategory_type, subcategory_id)

            if not subcategory_obj: continue


            offers = subcategory_div.parent.find_all('a', {'class': 'tc-item'})

            lots = self.__parse_lot_shortcuts(offers, subcategory_obj, False)


            if lots:
                if self.currency != lots[0].currency: self.currency = lots[0].currency


            for lot in lots: user_obj.add_lot(lot)


        return user_obj


    @_raise_if_acc_is_not_initiated
    def get_chat(self, chat_id: int, with_history: bool = True, locale: Literal['ru', 'en', 'uk'] | None = None) -> Chat:
        '''
        Получает информацию о личном чате.

        :param chat_id: Айди чата.
        :type chat_id: :obj:`int`
        :param with_history: Получать ли историю сообщений, defaults to True.
        :type with_history: :obj:`bool`, опционально.
        :param locale: Язык аккаунта, который будет установлен при запросе к FunPay, defaults to None.
        :type locale: :obj:`Literal['ru', 'en', 'uk']` | :obj:`None`, опционально.
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises Exception: Поднимается, если не удалось найти чат.
        :return: Объект чата.
        :rtype: :class:`Chat`
        '''
        url = f'https://funpay.com/chat/'

        params = {'node': chat_id}

        headers = {'accept': '*/*'}

        if not locale: locale = self.__chat_parse_locale

        response = self.method('get', url, params=params, headers=headers, raise_not_200=True, locale=locale)


        if locale: self.locale = self.__default_locale


        html_response = response.content.decode()

        parser = BeautifulSoup(html_response, 'lxml')


        if (name := parser.find('div', {'class': 'chat-header'}).find('div', {'class': 'media-user-name'}).find('a').text) in ('Чат', 'Chat'):
            raise Exception('chat not found') # TODO


        self.__update_app_data(parser)


        if not (chat_panel := parser.find('div', {'class': 'param-item chat-panel'})): text, link = None, None

        else:
            a = chat_panel.find('a')
            text, link = a.text, a['href']


        if with_history: history = self.get_chat_history(chat_id, interlocutor_username=name)

        else: history = []


        return Chat(chat_id, name, html_response, history, link, text)


    def get_order_shortcut(self, order_id: str) -> OrderShortcut: # TODO взаимодействие с покупками
        '''
        Получает краткую информацию о заказе.

        РАБОТАЕТ ТОЛЬКО ДЛЯ ПРОДАЖ.

        :param order_id: Айди заказа.
        :type order_id: :obj:`str`
        :return: Объект заказа.
        :rtype: :class:`OrderShortcut`
        '''
        return self.runner.saved_orders.get(order_id, self.get_sales(id=order_id)[1][0])


    @_raise_if_acc_is_not_initiated
    def get_order(self, order_id: str, locale: Literal['ru', 'en', 'uk'] | None = None) -> Order:
        '''
        Получает полную информацию о заказе.

        :param order_id: Айди заказа.
        :type order_id: str
        :param locale: Язык аккаунта, который будет установлен при запросе к FunPay, defaults to None.
        :type locale: Literal['ru', 'en', 'uk'] | None, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.UnauthorizedError`: Поднимается, если пользователь не авторизован.
        :return: Объект заказа.
        :rtype: Order
        '''
        url = f'https://funpay.com/orders/{order_id}/'

        headers = {'accept': '*/*'}

        if not locale: locale = self.__order_parse_locale

        response = self.method('get', url, headers=headers, raise_not_200=True, locale=locale)


        if locale: self.locale = self.__default_locale


        html_response = response.content.decode()

        parser = BeautifulSoup(html_response, 'lxml')


        username = parser.find('div', {'class': 'user-link-name'})

        if not username: raise exceptions.UnauthorizedError(response)


        self.__update_app_data(parser)


        if (span := parser.find('span', {'class': 'text-warning'})) and span.text in ('Возврат', 'Повернення', 'Refund'): status = OrderStatuses.REFUNDED

        elif (span := parser.find('span', {'class': 'text-success'})) and span.text in ('Закрыт', 'Закрито', 'Closed'): status = OrderStatuses.CLOSED

        else: status = OrderStatuses.PAID


        short_description = None

        full_description = None

        sum = None

        currency = Currencies.UNKNOWN

        subcategory = None

        order_secrets = []

        stop_params = False

        lot_params = []

        buyer_params = {}

        amount = 1


        for div in parser.find_all('div', {'class': 'param-item'}):
            if not (h := div.find('h5')): continue
    
            if not stop_params and div.find_previous('hr'): stop_params = True


            if h.text in ('Краткое описание', 'Короткий опис', 'Short description'):
                stop_params = True

                short_description = div.find('div').text


            elif h.text in ('Подробное описание', 'Докладний опис', 'Detailed description'):
                stop_params = True

                full_description = div.find('div').text


            elif h.text in ('Сумма', 'Сума', 'Total'):
                sum = float(div.find('span').text.replace(' ', ''))

                currency = Currencies(div.find('strong').text)


            elif h.text in ('Категория', 'Категорія', 'Category', 'Валюта', 'Currency'):
                subcategory_link = div.find('a').get('href')

                subcategory_split = subcategory_link.split('/')

                subcategory_id = int(subcategory_split[-2])

                subcategory_type = SubCategoryTypes.COMMON if 'lots' in subcategory_link else SubCategoryTypes.CURRENCY

                subcategory = self.get_subcategory(subcategory_type, subcategory_id)


            elif h.text in ('Оплаченный товар', 'Оплаченные товары', 'Оплачений товар', 'Оплачені товари', 'Paid product', 'Paid products'):
                secret_placeholders = div.find_all('span', class_='secret-placeholder')

                order_secrets = [i.text for i in secret_placeholders]


            elif h.text in ('Количество', 'Amount', 'Кількість'):
                div2 = div.find('div', class_='text-bold')

                if div2:
                    match = PRODUCTS_AMOUNT_RE.fullmatch(div2.text)

                    if match: amount = int(match.groupdict()['amount'].replace(' ', ''))


            elif h.text in ('Відкрито', 'Открыт', 'Open'): continue  # TODO


            elif h.text in ('Закрито', 'Закрыт', 'Closed'): continue  # TODO


            elif not stop_params and h.text not in ('Игра', 'Гра', 'Game'):
                div2 = div.find('div')

                if div2:
                    res = div2.text.strip()

                    lot_params.append((h.text, res))


            elif stop_params:
                div2 = div.find('div', class_='text-bold')

                if div2: buyer_params[h.text] = div2.text

        if not stop_params: lot_params = []


        chat = parser.find('div', {'class': 'chat-header'})

        chat_link = chat.find('div', {'class': 'media-user-name'}).find('a')


        interlocutor_name = chat_link.text

        interlocutor_id = int(chat_link.get('href').split('/')[-2])


        nav_bar = parser.find('ul', {'class': 'nav navbar-nav navbar-right logged'})

        active_item = nav_bar.find('li', {'class': 'active'})

        if any(i in active_item.find('a').text.strip() for i in ('Продажи', 'Продажі', 'Sales')):
            buyer_id, buyer_username = interlocutor_id, interlocutor_name

            seller_id, seller_username = self.id, self.username

        else:
            buyer_id, buyer_username = self.id, self.username

            seller_id, seller_username = interlocutor_id, interlocutor_name


        id1, id2 = sorted([buyer_id, seller_id])

        chat_id = f'users-{id1}-{id2}'


        review_obj = parser.find('div', {'class': 'order-review'})

        if not (stars_obj := review_obj.find('div', {'class': 'rating'})): stars, text = None, None

        else:
            stars = int(stars_obj.find('div').get('class')[0].split('rating')[1])

            text = review_obj.find('div', {'class': 'review-item-text'}).text.strip()


        hidden = review_obj.find('span', class_='text-warning') is not None


        if not (reply_obj := review_obj.find('div', {'class': 'review-item-answer review-compiled-reply'})): reply = None

        else: reply = reply_obj.find('div').text.strip()


        if all([not text, not reply]): review = None


        else:
            review = Review(
                stars,
                text,
                reply,
                False,
                str(review_obj),
                hidden,
                order_id,
                buyer_username,
                buyer_id,
                text and text.endswith(self.bot_character),
                reply and reply.endswith(self.bot_character)
            )


        order = Order(
            order_id,
            status,
            subcategory,
            lot_params,
            buyer_params,
            short_description,
            short_description,
            full_description,
            amount,
            sum,
            currency,
            buyer_id,
            buyer_username,
            seller_id,
            seller_username,
            chat_id,
            html_response,
            review,
            order_secrets
        )


        return order


    @_raise_if_acc_is_not_initiated
    def get_sales(
            self, start_from: str | None = None, include_paid: bool = True, include_closed: bool = True, include_refunded: bool = True, exclude_ids: list[str] | None = None,
            id: str | None = None, buyer: str | None = None, state: Literal['closed', 'paid', 'refunded'] | None = None, game: int | None = None, # TODO OrderStatuses
            section: str | None = None, server: int | None = None, side: int | None = None,
            locale: Literal['ru', 'en', 'uk'] | None = None,
            **more_filters
    ) -> tuple[str | None, list[OrderShortcut], dict[str, SubCategory]]:
        '''
        Получает и парсит список заказов со страницы https://funpay.com/orders/trade

        :param start_from: Айди заказа, с которого начать список, defaults to :obj:`None`.
        :type start_from: :obj:`str`
        :param include_paid: Включить ли в список заказы, ожидающие выполнения, defaults to :obj:`True`.
        :type include_paid: :obj:`bool`, опционально
        :param include_closed: Включить ли в список закрытые заказы, defaults to :obj:`True`.
        :type include_closed: :obj:`bool`, опционально
        :param include_refunded: Включить ли в список заказы, за которые запрошен возврат средств, defaults to :obj:`True`.
        :type include_refunded: :obj:`bool`, опционально
        :param exclude_ids: Исключить заказы с айди из списка, defaults to :obj:`None`.
        :type exclude_ids: :obj:`list[str]` | :obj:`None`, опционально
        :param id: Айди заказа, defaults to :obj:`None`.
        :type id: :obj:`str` | :obj:`None`, опционально
        :param buyer: Никнейм покупателя, defaults to :obj:`None`.
        :type buyer: :obj:`str` | :obj:`None`, опционально
        :param state: Статус заказа, defaults to :obj:`None`.
        :type state: :obj:`str` :obj:`Literal['paid', 'closed' or 'refunded']` | :obj:`None`, опционально
        :param game: Айди игры, defaults to :obj:`None`.
        :type game: :obj:`int` | :obj:`None`, опционально
        :param section: Айди категории в формате `<тип лота>-<айди категории>`, defaults to :obj:`None`.\n
            Типы лотов:\n
            * `lot` - стандартный лот (например: `lot-256`)\n
            * `chip` - игровая валюта (например: `chip-4471`)\n
        :type section: :obj:`str` | :obj:`None`, опционально
        :param server: Айди сервера, defaults to :obj:`None`.
        :type server: :obj:`int` | :obj:`None`, опционально
        :param side: Айди стороны (платформы), defaults to :obj:`None`.
        :type side: :obj:`int` | :obj:`None`, опционально
        :param locale: Язык аккаунта, который будет установлен при запросе к FunPay, defaults to :obj:`None`.
        :type locale: :obj:`Literal['ru', 'en', 'uk']` | :obj:`None`, опционально
        :param subcategories: Список подкатегорий, defaults to :obj:`None`.
        :type subcategories: :obj:`dict[str, tuple[SubCategoryTypes, int]]` | :obj:`None`, опционально
        :param more_filters: Доп. фильтры.
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.UnauthorizedError`: Поднимается, если пользователь не авторизован.
        :return: (Айди следующего заказа (для `start_from`), список заказов).
        :rtype: :obj:`tuple[str | None, list[OrderShortcut]]`
        '''
        exclude_ids = exclude_ids or []


        url = 'https://funpay.com/orders/trade'

        params = {
            'id': id,
            'buyer': buyer,
            'state': state,
            'game': game,
            'section': section,
            'server': server,
            'side': side
        }

        payload = more_filters.copy()

        if start_from: payload['continue'] = start_from

        locale = locale or self.__profile_parse_locale

        response = self.method('post' if start_from else 'get', url, params=params, payload=payload, raise_not_200=True, locale=locale)


        if not start_from: self.locale = self.__default_locale


        html_response = response.content.decode()

        parser = BeautifulSoup(html_response, 'lxml')


        if not start_from:
            username = parser.find('div', {'class': 'user-link-name'})

            if not username: raise exceptions.UnauthorizedError(response)


        next_order_id = parser.find('input', {'type': 'hidden', 'name': 'continue'})

        next_order_id = next_order_id.get('value') if next_order_id else None


        order_divs = parser.find_all('a', {'class': 'tc-item'})


        if not start_from: self.__update_app_data(parser)


        if not order_divs: return None, []


        subcategories: dict[str, SubCategory | None] = {}


        games_options = parser.find('select', attrs={'name': 'game'})

        if games_options:
            games_options = games_options.find_all(lambda x: x.name == 'option' and x.get('value'))

            for game_option in games_options:
                game_name = game_option.text

                sections_list = json.loads(game_option.get('data-data'))

                for key, section_name in sections_list:

                    section_type, section_id = key.split('-')

                    section_type = SubCategoryTypes.COMMON if section_type == 'lot' else SubCategoryTypes.CURRENCY

                    section_id = int(section_id)

                    subcategories[f'{game_name}, {section_name}'] = self.get_subcategory(section_type, section_id)


        sales = []

        for div in order_divs:
            classname = div.get('class')


            if 'warning' in classname:
                if not include_refunded: continue

                order_status = OrderStatuses.REFUNDED

            elif 'info' in classname:
                if not include_paid: continue

                order_status = OrderStatuses.PAID

            else:
                if not include_closed: continue

                order_status = OrderStatuses.CLOSED


            order_id = div.find('div', {'class': 'tc-order'}).text[1:]

            if order_id in exclude_ids: continue


            description = div.find('div', {'class': 'order-desc'}).find('div').text


            tc_price = div.find('div', {'class': 'tc-price'}).text

            price, currency = tc_price.rsplit(maxsplit=1)

            price = float(price.replace(' ', ''))

            currency = Currencies(currency)


            buyer_div = div.find('div', {'class': 'media-user-name'}).find('span')

            buyer_username = buyer_div.text

            buyer_id = int(buyer_div.get('data-href')[:-1].split('/users/')[1])


            subcategory_name = div.find('div', {'class': 'text-muted'}).text

            subcategory = subcategories.get(subcategory_name)


            now = datetime.now()

            order_date_text = div.find('div', {'class': 'tc-date-time'}).text

            if any(today in order_date_text for today in ('сегодня', 'сьогодні', 'today')):  # сегодня, ЧЧ:ММ
                h, m = order_date_text.split(', ')[1].split(':')

                order_date = datetime(now.year, now.month, now.day, int(h), int(m))

            elif any(yesterday in order_date_text for yesterday in ('вчера', 'вчора', 'yesterday')):  # вчера, ЧЧ:ММ
                h, m = order_date_text.split(', ')[1].split(':')

                temp = now - timedelta(days=1)

                order_date = datetime(temp.year, temp.month, temp.day, int(h), int(m))

            elif order_date_text.count(' ') == 2:  # ДД месяца, ЧЧ:ММ
                split = order_date_text.split(', ')

                day, month = split[0].split()

                day, month = int(day), Months[month]

                h, m = split[1].split(':')

                order_date = datetime(now.year, month.value, day, int(h), int(m))

            else:  # ДД месяца ГГГГ, ЧЧ:ММ
                split = order_date_text.split(', ')

                day, month, year = split[0].split()

                day, month, year = int(day), Months[month], int(year)

                h, m = split[1].split(':')

                order_date = datetime(year, month.value, day, int(h), int(m))


            id1, id2 = sorted([buyer_id, self.id])

            chat_id = f'users-{id1}-{id2}'


            order_obj = OrderShortcut(
                order_id,
                description,
                price,
                currency,
                buyer_username,
                buyer_id,
                chat_id,
                order_status,
                order_date,
                subcategory_name,
                subcategory,
                str(div)
            )

            sales.append(order_obj)


        return next_order_id, sales, subcategories


    def add_chats(self, chats: list[ChatShortcut]) -> None:
        '''
        Сохраняет чаты.

        :param chats: Список чатов.
        :type chats: :obj:`list[ChatShortcut]`
        '''
        self.__saved_chats.update({chat.id: chat for chat in chats})


    @_raise_if_acc_is_not_initiated
    def request_chats(self) -> list[ChatShortcut]:
        '''
        Запрашивает чаты и парсит их.

        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :return: Объекты чатов (не больше 50).
        :rtype: list[ChatShortcut]
        '''
        chats_data = RunnerObject(
            'chat_bookmarks',
            self.id,
            generate_random_tag()
        )

        payload = RunnerPayload(
            [chats_data]
        )

        response = self.runner.send_request(payload)

        response_obj = RunnerResponse.from_json(response.json())


        for obj in response_obj.objects:
            if obj.type == 'chat_bookmarks':
                msgs = obj.data['html']

                break

        else: return []


        parser = BeautifulSoup(msgs, 'lxml')
    
        chats = parser.find_all('a', {'class': 'contact-item'})


        chats_objs = [
            ChatShortcut(
                int(msg['data-id']),
                msg.find('div', {'class': 'media-user-name'}).text,
                (
                    last_msg_text if not (last_msg_text:=msg.find('div', {'class': 'contact-item-message'}).text).startswith(self.bot_character) else
                    last_msg_text[1:]
                ),
                int(msg.get('data-node-msg')),
                int(msg.get('data-user-msg')),
                True if 'unread' in msg.get('class') else False,
                str(msg),
                True if last_msg_text.startswith(self.bot_character) else False
            ) for msg in chats
        ]


        return chats_objs


    @_raise_if_acc_is_not_initiated
    def get_chats(self, update: bool = False) -> dict[int, ChatShortcut]:
        '''
        Возвращает словарь с сохраненными чатами.

        :param update: Обновить список чатов, defaults to :obj:`False`.
        :type update: :obj:`bool`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :return: Словарь с сохраненными чатами.
        :rtype: :obj:`dict[int, ChatShortcut]`
        '''
        if update:
            chats = self.request_chats()

            self.add_chats(chats)


        return self.__saved_chats


    @_raise_if_acc_is_not_initiated
    def get_chat_by_name(self, name: str, make_request: bool = False) -> ChatShortcut | None:
        '''
        Возвращает чат по его названию.

        :param name: Название чата.
        :type name: :obj:`str`
        :param make_request: Обновить ли сохраненные чаты, если чат не был найден, defaults to :obj:`False`.
        :type make_request: :obj:`bool`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :return: Объект чата.
        :rtype: :class:`ChatShortcut` | :obj:`None`
        '''
        for chat in self.__saved_chats:
            if self.__saved_chats[chat].name == name: return self.__saved_chats[chat]


        if make_request:
            self.add_chats(self.request_chats())

            return self.get_chat_by_name(name)

        else: return None


    @_raise_if_acc_is_not_initiated
    def get_chat_by_id(self, chat_id: int, make_request: bool = False) -> ChatShortcut | None:
        '''
        Возвращает чат по его айди.

        :param chat_id: Айди чата.
        :type chat_id: :obj:`int`
        :param make_request: Обновить ли сохраненные чаты, если чат не был найден, defaults to :obj:`False`.
        :type make_request: :obj:`bool`, опционально
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :return: Объект чата.
        :rtype: :class:`ChatShortcut` | :obj:`None`
        '''
        if not make_request or chat_id in self.__saved_chats: return self.__saved_chats.get(chat_id)


        self.add_chats(self.request_chats())

        return self.get_chat_by_id(chat_id)


    @_raise_if_acc_is_not_initiated
    def calc(self, subcategory_type: SubCategoryTypes, subcategory_id: int | None = None, game_id: int | None = None, price: int | float = 1000) -> CalcResult:
        '''
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        '''
        if subcategory_type == SubCategoryTypes.COMMON:
            key = 'nodeId'
            type = 'lots'
            value = subcategory_id

        else:
            key = 'game'
            type = 'chips'
            value = game_id


        url = f'https://funpay.com/{type}/calc'

        headers = {
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'x-requested-with': 'XMLHttpRequest'
        }

        payload = {key: value, 'price': price}


        response = self.method('post', url, headers=headers, payload=payload, raise_not_200=True)


        json_response = response.json()


        if (error := json_response.get('error')): raise Exception(f'Произошел бабах, не нашелся ответ: {error}')  # TODO


        methods = []

        for method in json_response.get('methods'):
            methods.append(
                PaymentMethod(
                    method.get('name'),
                    float(method['price'].replace(' ', '')),
                    Currencies(method.get('unit')),
                    method.get('sort')
                )
            )


        if 'minPrice' in json_response:
            min_price, min_price_currency = json_response['minPrice'].rsplit(' ', maxsplit=1)

            min_price = float(min_price.replace(' ', ''))

            min_price_currency = Currencies(min_price_currency)

        else: min_price, min_price_currency = None, Currencies.UNKNOWN


        return CalcResult(
            subcategory_type,
            subcategory_id,
            methods,
            price,
            min_price,
            min_price_currency,
            self.currency
        )


    @_raise_if_acc_is_not_initiated
    def get_lot_fields(self, lot_id: int) -> LotFields:
        '''
        Получает все поля лота.

        :param lot_id: Айди лота.
        :type lot_id: :obj:`int`
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.LotParsingError`: Поднимается, если при получении полей лота возникла ошибка.
        :return: Поля лота.
        :rtype: :class:`LotFields`
        '''
        url = f'https://funpay.com/lots/offerEdit'

        params = {'offer': lot_id}

        headers = {}

        response = self.method('get', url, params=params, headers=headers, raise_not_200=True)


        html_response = response.content.decode()

        parser = BeautifulSoup(html_response, 'lxml')


        error_message = parser.find('p', class_='lead')

        if error_message: raise exceptions.LotParsingError(response, error_message.text, lot_id)


        result = {}

        result.update(
            {
                field['name']: field.get('value') or ''
                for field in parser.find_all('input')
                if field['name'] != 'query'
            }
        )

        result.update(
            {
                field['name']: field.text or ''
                for field in parser.find_all('textarea')
            }
        )

        result.update(
            {
                field['name']: field.find('option', selected=True)['value']
                for field in parser.find_all('select')
                if 'hidden' not in field.find_parent(class_='form-group').get('class', [])
            }
        )

        result.update(
            {
                field['name']: 'on'
                for field in parser.find_all('input', {'type': 'checkbox'}, checked=True)
            }
        )


        subcategory = self.get_subcategory(SubCategoryTypes.COMMON, int(result.get('node_id', 0)))


        self.csrf_token = result.get('csrf_token') or self.csrf_token


        currency = Currencies(parser.find('span', class_='form-control-feedback').text)

        if self.currency != currency: self.currency = currency


        bs_buyer_prices = parser.find('table', class_='table-buyers-prices').find_all('tr')

        payment_methods = []

        for _, pm in enumerate(bs_buyer_prices):
            pm_price, pm_currency = pm.find('td').text.rsplit(maxsplit=1)

            pm_price = float(pm_price.replace(' ', ''))

            pm_currency = Currencies(pm_currency)


            payment_methods.append(PaymentMethod(pm.find('th').text, pm_price, pm_currency, _))


        calc_result = CalcResult(
            SubCategoryTypes.COMMON,
            subcategory.id,
            payment_methods,
            float(result['price']),
            None,
            Currencies.UNKNOWN,
            currency
        )


        return LotFields(result, lot_id, subcategory, currency, calc_result)


    @_raise_if_acc_is_not_initiated
    def get_chip_fields(self, subcategory_id: int) -> ChipFields:
        '''
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        '''
        url = f'https://funpay.com/chips/{subcategory_id}/trade'

        headers = {}

        response = self.method('get', url, headers=headers, raise_not_200=True)


        html_response = response.content.decode()

        parser = BeautifulSoup(html_response, 'lxml')


        result = {
            field['name']: field.get('value') or ''
            for field in parser.find_all('input')
            if field['name'] != 'query'
        }

        result.update(
            {
                field['name']: 'on'
                for field in parser.find_all('input', {'type': 'checkbox'}, checked=True)
            }
        )


        return ChipFields(result, self.id, subcategory_id)


    @_raise_if_acc_is_not_initiated
    def save_offer(self, offer_fields: LotFields | ChipFields) -> None:
        '''
        Сохраняет лот на FunPay.

        :param offer_fields: Поля лота.
        :type offer_fields: :class:`LotFields` | :class:`ChipFields`
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        :raises :class:`common.exceptions.LotSavingError`: Поднимается, если при сохранении лота возникла ошибка.
        '''
        url = f'https://funpay.com/{'lots/offerSave' if isinstance(offer_fields, LotFields) else 'chips/saveOffers'}'

        headers = {
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'x-requested-with': 'XMLHttpRequest',
        }

        offer_fields.csrf_token = self.csrf_token

        fields = offer_fields.fields

        offer_id = offer_fields.lot_id if isinstance(offer_fields, LotFields) else offer_fields.subcategory_id

        response = self.method('post', url, headers=headers, payload=fields, raise_not_200=True)


        json_response = response.json()


        if (errors := json_response.get('errors')) or json_response.get('error'):
            if errors:
                errors_dict = {}

                for k, v in errors: errors_dict.update({k: v})


            raise exceptions.LotSavingError(response, json_response.get('error'), offer_id, errors_dict)


    def delete_lot(self, lot_id: int) -> None:
        '''
        Удаляет лот.

        :param lot_id: Айди лота.
        :type lot_id: :obj:`int`
        '''
        self.save_offer(LotFields({'csrf_token': self.csrf_token, 'offer_id': lot_id, 'deleted': '1'}, lot_id))


    def get_exchange_rate(self, currency: Currencies) -> tuple[float, Currencies]:
        '''
        Получает курс обмена текущей валюты аккаунта на переданную, обновляет валюту аккаунта.

        :param currency: Валюта, на которую нужно получить курс обмена.
        :type currency: :class:`Currencies`
        :return: Кортеж, содержащий коэффициент обмена и текущую валюту аккаунта.
        :rtype: :obj:`tuple[float, Currencies]`
        '''
        url = f'https://funpay.com/account/switchCurrency'

        headers = {
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'x-requested-with': 'XMLHttpRequest'
        }

        payload = {'cy': currency.name.lower(), 'csrf_token': self.csrf_token, 'confirmed': 'false'}

        response = self.method('post', url, headers=headers, payload=payload, raise_not_200=True)


        json_response = json.loads(response.text)


        if 'url' in json_response and not json_response['url']:
            self.currency = currency


            return 1, currency

        else:
            parser = BeautifulSoup(json_response['modal'], 'lxml').find('p', class_='lead').text.replace('\xa0', ' ')

            match = EXCHANGE_RATE_RE.fullmatch(parser)


            price1 = float(match.groupdict()['exchange_rate_currency_from'])

            currency1 = Currencies(match.groupdict()['currency_from_symbol'])


            price2 = float(match.groupdict()['exchange_rate_currency_to'])

            currency2 = Currencies(match.groupdict()['currency_to_symbol'])

            now_currency = ({currency1, currency2} - {currency, }).pop()

            self.currency = now_currency


            if now_currency == currency1: return price2 / price1, now_currency

            else: return price1 / price2, now_currency


    def get_category(self, category_id: int) -> Category | None:
        '''
        Возвращает объект категории (игры).

        :param category_id: Айди категории (игры).
        :type category_id: :obj:`int`
        :return: Объект категории (игры).
        :rtype: :class:`Category` | :obj:`None`
        '''
        return self.__sorted_categories.get(category_id)


    @property
    def categories(self) -> list[Category]:
        '''
        Все категории (игры) FunPay.
        '''
        return self.__categories


    def get_sorted_categories(self) -> dict[int, Category]:
        '''
        Все категории (игры) FunPay в виде словаря {айди: категория}.
        '''
        return self.__sorted_categories


    def get_subcategory(self, subcategory_type: SubCategoryTypes, subcategory_id: int) -> SubCategory | None:
        '''
        Возвращает объект подкатегории.

        :param subcategory_type: Тип подкатегории.
        :type subcategory_type: :class:`SubCategoryTypes`
        :param subcategory_id: Айди подкатегории.
        :type subcategory_id: :obj:`int`
        :return: Подкатегория.
        :rtype: :class:`SubCategory` | :obj:`None`
        '''
        return self.__sorted_subcategories[subcategory_type].get(subcategory_id)


    @property
    def subcategories(self) -> list[SubCategory]:
        '''
        Все подкатегории FunPay.
        '''
        return self.__subcategories


    def get_sorted_subcategories(self) -> dict[SubCategoryTypes, dict[int, SubCategory]]:
        '''
        Все подкатегории FunPay в виде словаря {тип подкатегории: {айди: подкатегория}}.

        :return: все подкатегории FunPay в виде словаря {тип подкатегории: {айди: подкатегория}}
        :rtype: :obj:`dict[SubCategoryTypes, dict[int, SubCategory]]`
        '''
        return self.__sorted_subcategories


    @_raise_if_acc_is_not_initiated
    def logout(self) -> None:
        '''
        Выходит с аккаунта FunPay (сбрасывает :obj:`golden_key`).
        :raises :class:`common.exceptions.AccountNotInitiatedError`: Поднимается, если аккаунт не был инициализирован.
        '''
        self.method('get', self._logout_link, headers={'accept': '*/*'}, raise_not_200=True)


    @property
    def is_initiated(self) -> bool:
        '''
        Инициализирован ли класс :class:`Account` с помощью метода :meth:`get`.
        '''
        return self.__initiated


    def __setup_categories(self, html: str):
        '''
        Парсит категории и подкатегории с основной страницы и добавляет их в свойства класса.

        :param html: HTML страница.
        '''
        parser = BeautifulSoup(html, 'lxml')


        games_table = parser.find_all('div', {'class': 'promo-game-list'})

        if not games_table: return


        games_table = games_table[1] if len(games_table) > 1 else games_table[0]

        game_divs = games_table.find_all('div', {'class': 'promo-game-item'})

        if not game_divs: return


        game_position = 0

        subcategory_position = 0

        for game_div in game_divs:
            game_id = int(game_div.find('div', {'class': 'game-title'}).get('data-id'))

            game_name = game_div.find('a').text

            regional_games = {game_id: Category(game_id, game_name, position=game_position)}

            game_position += 1


            if regional_divs := game_div.find('div', {'role': 'group'}):
                for btn in regional_divs.find_all('button'):
                    regional_game_id = int(btn['data-id'])

                    regional_games[regional_game_id] = Category(regional_game_id, f'{game_name} ({btn.text})', position=game_position)

                    game_position += 1


            subcategories_divs = game_div.find_all('ul', {'class': 'list-inline'})

            for subcategories_div in subcategories_divs:
                subcategory_game_id = int(subcategories_div['data-id'])

                subcategories = subcategories_div.find_all('li')

                for subcategory_div in subcategories:
                    subcategory_name_div = subcategory_div.find('a')

                    name, link = subcategory_name_div.text, subcategory_name_div['href']

                    subcategory_type = SubCategoryTypes.CURRENCY if 'chips' in link else SubCategoryTypes.COMMON

                    subcategory_id = int(link.split('/')[-2])

                    subcategory_obj = SubCategory(
                        subcategory_id,
                        name,
                        subcategory_type,
                        regional_games[subcategory_game_id],
                        subcategory_position
                    )

                    subcategory_position += 1

                    regional_games[subcategory_game_id].add_subcategory(subcategory_obj)

                    self.__subcategories.append(subcategory_obj)

                    self.__sorted_subcategories[subcategory_type][subcategory_id] = subcategory_obj


            for game_id in regional_games:
                self.__categories.append(regional_games[game_id])

                self.__sorted_categories[game_id] = regional_games[game_id]


    def __parse_messages(
        self, json_messages: dict, chat_id: int | str,
        interlocutor_id: Optional[int] = None, interlocutor_username: Optional[str] = None,
        from_id: int = 0
    ) -> list[Message]:
        messages: list[Message] = []

        ids = {self.id: self.username, 0: 'FunPay'}
        badges: dict[int, str | None] = {}
        if None not in (interlocutor_id, interlocutor_username):
            ids[interlocutor_id] = interlocutor_username

        for json_message in json_messages:
            if json_message['id'] < from_id: continue


            author_id = json_message['author']


            parser = BeautifulSoup(json_message['html'].replace('<br>', '\n'), 'lxml')


            # Если ник или бейдж написавшего неизвестен, но есть блок с данными об авторе сообщения
            if None in [ids.get(author_id), badges.get(author_id)] and (author_div := parser.find('div', {'class': 'media-user-name'})):
                if badges.get(author_id) is None:
                    badge = author_div.find('span', {'class': 'chat-msg-author-label label label-success'})

                    badges[author_id] = badge.text if badge else 0


                if ids.get(author_id) is None:
                    author = author_div.find('a').text.strip()

                    ids[author_id] = author


                    if self.chat_id_private(chat_id):
                        if author_id == interlocutor_id and not interlocutor_username: interlocutor_username = author

                        elif interlocutor_username == author and not interlocutor_id: interlocutor_id = author_id


            by_bot = False

            image_name = None

            if self.chat_id_private(chat_id) and (image_tag := parser.find('a', {'class': 'chat-img-link'})):
                image_name = image_tag.find('img')

                image_name = image_name.get('alt') if image_name else None

                image_link = image_tag.get('href')

                message_text = None


                if isinstance(image_name, str) and 'crd_ext' in image_name.lower(): by_bot = True

            else:
                image_link = None

                if author_id == 0: message_text = parser.find('div', role='alert').text.strip()

                else: message_text = parser.find('div', {'class': 'chat-msg-text'}).text


                if message_text.startswith(self.__bot_character) and author_id == self.id:
                    message_text = message_text[1:]

                    by_bot = True


            badge = badges.get(author_id) or None

            default_label = parser.find('div', {'class': 'media-user-name'})

            default_label = default_label.find('span', {'class': 'chat-msg-author-label label label-default'}) if default_label else None

            badge: str | None = default_label.text if (badge is None and default_label is not None) else badge


            is_employee = True if badge else False
            is_support = True if (badge and badge in ('поддержка', 'підтримка', 'support')) else False
            is_moderation = True if (badge and badge in ('модерация', 'модерація', 'moderation')) else False
            is_arbitration = True if (badge and badge in ('арбитраж', 'арбітраж', 'arbitration')) else False
            is_autoreply = True if (default_label and default_label.text in ('автовідповідь', 'автоответ', 'auto-reply')) else False


            message_obj = Message(
                json_message['id'],
                message_text,
                chat_id,
                interlocutor_username,
                interlocutor_id,
                ids.get(author_id),
                author_id,
                json_message['html'],
                None, # TODO BuyerViewing
                by_bot,
                image_link,
                image_name,
                badge,
                is_employee,
                is_support,
                is_moderation,
                is_arbitration,
                is_autoreply
            )

            messages.append(message_obj)


        for message in messages:
            parser = BeautifulSoup(message.html, 'lxml')


            if message.type is not MessageTypes.NON_SYSTEM:
                users = parser.find_all('a', href=lambda href: href and '/users/' in href)

                if users:
                    message.initiator_username = users[0].text

                    message.initiator_id = int(users[0]['href'].split('/')[-2])


                    if message.type in (
                        MessageTypes.ORDER_PURCHASED,
                        MessageTypes.ORDER_CONFIRMED,
                        MessageTypes.NEW_FEEDBACK,
                        MessageTypes.FEEDBACK_CHANGED,
                        MessageTypes.FEEDBACK_DELETED
                    ):
                        if message.initiator_id == self.id:
                            message.i_am_seller = False

                            message.i_am_buyer = True

                        else:
                            message.i_am_seller = True

                            message.i_am_buyer = False

                    elif message.type in (
                        MessageTypes.NEW_FEEDBACK_ANSWER,
                        MessageTypes.FEEDBACK_ANSWER_CHANGED,
                        MessageTypes.FEEDBACK_ANSWER_DELETED,
                        MessageTypes.REFUND
                    ):
                        if message.initiator_id == self.id:
                            message.i_am_seller = True

                            message.i_am_buyer = False

                        else:
                            message.i_am_seller = False

                            message.i_am_buyer = True

                    elif len(users) > 1:
                        last_user_id = int(users[-1]['href'].split('/')[-2])

                        if message.type == MessageTypes.ORDER_CONFIRMED_BY_ADMIN:
                            if last_user_id == self.id:
                                message.i_am_seller = True

                                message.i_am_buyer = False

                            else:
                                message.i_am_seller = False

                                message.i_am_buyer = True

                        elif message.type == MessageTypes.REFUND_BY_ADMIN:
                            if last_user_id == self.id:
                                message.i_am_seller = False

                                message.i_am_buyer = True

                            else:
                                message.i_am_seller = True

                                message.i_am_buyer = False


        return messages


    @staticmethod
    def __parse_lot_shortcuts(offers: list[Tag], subcategory_obj: SubCategory, public_lots: bool = False, my_lots: bool = False) -> list[LotShortcut] | list[MyLotShortcut]:
        result = []

        sellers = {}


        for offer in offers:
            promo = None

            seller = None

            attributes = None



            offer_id = offer['data-offer'] if my_lots else offer['href'].split('id=')[1]


            if my_lots: active = 'warning' not in offer.get('class', [])


            if public_lots: promo = 'offer-promo' in offer.get('class', [])


            description = offer.find('div', {'class': 'tc-desc-text'})

            description = description.text if description else None


            server = offer.find('div', {'class':'tc-server'})

            server = server.text if server else None


            side = offer.find('div', {'class': 'tc-side'})

            side = side.text if side else None


            tc_price = offer.find('div', {'class': 'tc-price'})


            if subcategory_obj.type is SubCategoryTypes.COMMON or my_lots: price = float(tc_price['data-s'])

            else: price = float(tc_price.find('div').text.rsplit(maxsplit=1)[0].replace(' ', ''))


            currency = Currencies(tc_price.find('span', {'class': 'unit'}).text)


            tc_amount = offer.find('div', {'class': 'tc-amount'})

            amount = tc_amount.text.replace(' ', '') if tc_amount else None

            amount = int(amount) if amount and amount.isdigit() else None



            if not public_lots: auto = offer.find('i', class_='auto-dlv-icon') is not None


            if public_lots:
                seller_soup = offer.find('div', {'class': 'tc-user'})

                seller_key = str(seller_soup)


                attributes = {
                    k.replace('data-', '', 1): int(v) if v.isdigit() else v
                    for k, v in offer.attrs.items()
                    if k.startswith('data-')
                }

                auto = attributes.get('auto') == 1


                if seller_key not in sellers: sellers[seller_key] = Account.__parse_seller_shortcut(offer, seller_key, attributes)

                seller = sellers[seller_key]


            lot_obj = (
                MyLotShortcut(
                    offer_id,
                    server,
                    side,
                    description,
                    description,
                    amount,
                    price,
                    currency,
                    subcategory_obj,
                    auto,
                    active,
                    str(offer)
                ) if my_lots else

                LotShortcut(
                    offer_id,
                    server,
                    side,
                    description,
                    description,
                    amount,
                    price,
                    currency,
                    subcategory_obj,
                    seller,
                    auto,
                    promo,
                    attributes,
                    str(offer)
                )
            )


            result.append(lot_obj)


        return result


    @staticmethod
    def __parse_seller_shortcut(offer: Tag, seller_key: str, attributes: dict) -> SellerShortcut:
        online = False

        if attributes.get('online') == 1: online = True


        seller_body = offer.find('div', {'class': 'media-body'})

        username = seller_body.find('div', {'class': 'media-user-name'}).text.strip()

        rating_stars = seller_body.find('div', {'class': 'rating-stars'})

        if rating_stars is not None: rating_stars = len(rating_stars.find_all('i', {'class': 'fas'}))

        k_reviews = seller_body.find('div', {'class': 'media-user-reviews'})

        if k_reviews: k_reviews = ''.join([i for i in k_reviews.text if i.isdigit()])

        k_reviews = int(k_reviews) if k_reviews else 0

        user_id = int(seller_body.find('span', {'class': 'pseudo-a'})['data-href'].split('/')[-2])


        return SellerShortcut(user_id, username, online, rating_stars, k_reviews, seller_key)


    @staticmethod
    def __parse_buyer_viewing(json_response: dict) -> BuyerViewing:
        buyer_id = json_response.get('id')


        if not json_response['data']: return BuyerViewing(buyer_id)


        tag = json_response['tag']


        html = json_response['data']['html']

        if html:
            html = html['desktop']

            element = BeautifulSoup(html, 'lxml').find('a')

            link, text = element.get('href'), element.text

        else: html, link, text = None, None, None


        return BuyerViewing(buyer_id, link, text, tag, html)


    def __update_app_data(self, parser: BeautifulSoup, get_user_id: bool = False, get_locale: bool = False, get_csrf_token: bool = True):
        try: 
            app_data = json.loads(parser.find('body').get('data-app-data'))


            if get_locale: self.__locale = app_data.get('locale')

            if get_user_id: self.id = app_data['userId']

            if get_csrf_token: self.csrf_token = app_data['csrf-token']


            self.app_data = app_data

            return app_data


        except:
            logger.warning('Произошла ошибка при считывании app-data.')
            logger.debug('TRACEBACK', exc_info=True)


    @staticmethod
    def chat_id_private(chat_id: int | str): return isinstance(chat_id, int) or PRIVATE_CHAT_ID_RE.fullmatch(chat_id)

    @property
    def bot_character(self) -> str: return self.__bot_character

    @property
    def locale(self) -> Literal['ru', 'en', 'uk'] | None: return self.__locale

    @locale.setter
    def locale(self, new_locale: Literal['ru', 'en', 'uk']):
        if self.__locale != new_locale and new_locale in ('ru', 'en', 'uk'): self.__set_locale = new_locale


__all__ = [
    'Account'
]