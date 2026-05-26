
from . import (
    DISCORD_RE, DEAR_VENDORS_RE, ORDER_PURCHASED_RE, ORDER_CONFIRMED_RE, NEW_FEEDBACK_RE, NEW_FEEDBACK_ANSWER_RE, FEEDBACK_CHANGED_RE, FEEDBACK_DELETED_RE, REFUND_RE,
    FEEDBACK_ANSWER_CHANGED_RE, FEEDBACK_ANSWER_DELETED_RE, ORDER_CONFIRMED_BY_ADMIN_RE, PARTIAL_REFUND_RE, ORDER_REOPENED_RE, REFUND_BY_ADMIN_RE
)


from enum import Enum


# ---------------------------------------------------------------------------- #
#                             Перечисления (Enums)                             #
# ---------------------------------------------------------------------------- #
class EventTypes(Enum):
    '''
    В данном классе перечислены все типы событий FunPayAPI.
    '''
    INITIAL_CHAT = 1
    'Обнаружен чат (при первом запросе Runner\'а).'

    CHATS_LIST_CHANGED = 2
    'Список чатов и/или последнее сообщение одного/нескольких чатов изменилось.'

    LAST_CHAT_MESSAGE_CHANGED = 3
    'В чате изменилось последнее сообщение.'

    NEW_MESSAGE = 4
    'Обнаружено новое сообщение в истории чата.'

    INITIAL_ORDER = 5
    'Обнаружен заказ (при первом запросе Runner\'а).'

    ORDERS_LIST_CHANGED = 6
    'Список заказов и/или статус одного/нескольких заказов изменился.'

    NEW_ORDER = 7
    'Новый заказ.'

    ORDER_STATUS_CHANGED = 8
    'Статус заказа изменился.'


class MessageTypes(Enum):
    '''
    В данном классе перечислены все типы сообщений.
    '''
    NON_SYSTEM = 1
    'Несистемное сообщение.'


    ORDER_PURCHASED = ORDER_PURCHASED_RE
    'Покупатель {buyer} оплатил заказ #{order_id}. Лот. X, не забудьте потом нажать кнопку «Подтвердить выполнение заказа» или «Подтвердить получение валюты».'


    ORDER_CONFIRMED = ORDER_CONFIRMED_RE
    'Покупатель X подтвердил успешное выполнение заказа #Y и отправил деньги продавцу Z.'


    NEW_FEEDBACK = NEW_FEEDBACK_RE
    'Покупатель X написал отзыв к заказу #Y.'


    FEEDBACK_CHANGED = FEEDBACK_CHANGED_RE
    'Покупатель X изменил отзыв к заказу #Y.'


    FEEDBACK_DELETED = FEEDBACK_DELETED_RE
    'Покупатель X удалил отзыв к заказу #Y.'


    NEW_FEEDBACK_ANSWER = NEW_FEEDBACK_ANSWER_RE
    'Продавец Z ответил на отзыв к заказу #Y.'


    FEEDBACK_ANSWER_CHANGED = FEEDBACK_ANSWER_CHANGED_RE
    'Продавец Z изменил ответ на отзыв к заказу #Y.'


    FEEDBACK_ANSWER_DELETED = FEEDBACK_ANSWER_DELETED_RE
    'Продавец Z удалил ответ на отзыв к заказу #Y.'

    ORDER_REOPENED = ORDER_REOPENED_RE
    'Заказ #Y открыт повторно.'

    REFUND = REFUND_RE
    'Продавец Z вернул деньги покупателю X по заказу #Y.'

    PARTIAL_REFUND = PARTIAL_REFUND_RE
    'Часть средств по заказу #Y возвращена покупателю.'

    ORDER_CONFIRMED_BY_ADMIN = ORDER_CONFIRMED_BY_ADMIN_RE
    'Администратор A подтвердил успешное выполнение заказа #Y и отправил деньги продавцу Z.'

    DISCORD = DISCORD_RE
    'Вы можете перейти в Discord. Внимание: общение за пределами сервера FunPay считается нарушением правил.'

    DEAR_VENDORS = DEAR_VENDORS_RE
    'Уважаемые продавцы, не доверяйте сообщениям в чате! Перед выполнением заказа всегда проверяйте наличие оплаты в разделе «Мои продажи».'

    REFUND_BY_ADMIN = REFUND_BY_ADMIN_RE
    'Администратор A вернул деньги покупателю X по заказу #Y.'


class OrderStatuses(Enum):
    '''
    В данном классе перечислены все состояния заказов.
    '''
    PAID = 1
    'Заказ оплачен и ожидает выполнения.'
    CLOSED = 2
    'Заказ закрыт.'
    REFUNDED = 3
    'Средства по заказу возвращены.'


class SubCategoryTypes(Enum):
    '''
    В данном классе перечислены все типы подкатегорий.
    '''
    COMMON = 1
    'Подкатегория со стандартными лотами.'
    CURRENCY = 2
    'Подкатегория с лотами игровой валюты (их нельзя поднимать).'


class Wallets(Enum):
    '''
    В данном классе перечислены все кошельки для вывода средств с баланса FunPay.
    '''
    QIWI = 1
    'Qiwi кошелек.'
    BINANCE = 2
    'Binance Pay.'
    TRC = 3
    'USDT TRC20.'
    CARD_RUB = 4
    'Рублевая банковская карта.'
    CARD_USD = 5
    'Долларовая банковская карта.'
    CARD_EUR = 6
    'Евро банковская карта.'
    WEBMONEY = 7
    'WebMoney WMZ.'
    YOUMONEY = 8
    'ЮMoney.'



class Currencies(Enum):
    '''
    В данном классе перечислены все типы валют баланса FunPay.
    '''
    USD = '$'
    'Доллар'
    RUB = '₽'
    'Рубль'
    EUR = '€'
    'Евро'
    UNKNOWN = '¤'
    'Неизвестная валюта'


class Months(Enum):
    '''
    Названия месяцев на FunPay.
    '''
    January = 1
    января = 1
    січня = 1

    February = 2
    февраля = 2
    лютого = 2

    March = 3
    марта = 3
    березня = 3

    April = 4
    апреля = 4
    квітня = 4

    May = 5
    мая = 5
    травня = 5

    June = 6
    июня = 6
    червня = 6

    July = 7
    июля = 7
    липня = 7

    August = 8
    августа = 8
    серпня = 8

    September = 9
    сентября = 9
    вересня = 9

    October = 10
    октября = 10
    жовтня = 10

    November = 11
    ноября = 11
    листопада = 11

    December = 12
    декабря = 12
    грудня = 12


class FloodErrorTexts(Enum):
    ru = 'Нельзя отправлять сообщения слишком часто.'
    en = 'You cannot send messages too frequently.'
    uk = 'Не можна надсилати повідомлення занадто часто.'


class MultiuserFloodErrorTexts(Enum):
    ru = 'Нельзя слишком часто отправлять сообщения разным пользователям.'
    en = 'Не можна надто часто надсилати повідомлення різним користувачам.'
    uk = 'You cannot message multiple users too frequently.'


__all__ = [
    'EventTypes',
    'MessageTypes',
    'OrderStatuses',
    'SubCategoryTypes',
    'Currencies',
    'Wallets',
    'Months',
    'FloodErrorTexts',
    'MultiuserFloodErrorTexts'
]