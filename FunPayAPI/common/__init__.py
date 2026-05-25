
from __future__ import annotations


from . import exceptions


import string
import random


def generate_random_tag() -> str:
    """
    Генерирует случайный тег для запроса (для runner'а).

    :return: сгенерированный тег.
    """
    return "".join(random.choice(string.digits + string.ascii_lowercase) for _ in range(10))


import re


# ---------------------------------------------------------------------------- #
#                           Регулярные выражения (re)                          #
# ---------------------------------------------------------------------------- #
PRIVATE_CHAT_ID_RE = re.compile(r'users-(?P<user_1>\d+)-(?P<user_2>\d+)$')
'''
Скомпилированное регулярное выражение, описывающее айди чата вида users-{айди-1}-{айди-2}.

Доступные группы match: `user_1`, `user_2`
'''


ORDER_ID_RE = re.compile(
    r'#(?P<order_id>[A-Z0-9]{8})'
)
'''
Скомпилированное регулярное выражение, описывающее ID заказа.

Доступные группы match: `order_id`.
'''


PRODUCTS_AMOUNT_RE = re.compile(
    r'(?P<amount>\d{1,3}(?: ?\d{3})*) (?:шт|pcs)\.'
)
'''
Скомпилированное регулярное выражение, описывающее запись кол-ва товаров в заказе.

Доступные группы match: `amount`.
'''


ORDER_PURCHASED_RE = re.compile(
    r'(?:Покупатель|The buyer) (?P<buyer>[a-zA-Z0-9]+) '
    r'(?:оплатил заказ|has paid for order) #(?P<order_id>[A-Z0-9]{8})\. '
    r'(?P<lot>.*?)\s'
    r'\1, '
    r'(?:'
        r'не забудьте потом нажать кнопку (?:«Подтвердить выполнение заказа»|«Подтвердить получение валюты»)\.|'
        r'do not forget to press the (?:«Confirm order fulfilment»|«Confirm currency receipt») button once you finish\.'
    r')'
)
'''
Скомпилированное регулярное выражение, описывающее сообщение об оплате заказа. Лучше всего использовать вместе с ORDER_PURCHASED2_RE.

Доступные группы match: `buyer`, `order_id`, `lot`.
'''


ORDER_CONFIRMED_RE = re.compile(
    r'(?:Покупатель|The buyer) (?P<buyer>[a-zA-Z0-9]+) '

    r'(?:подтвердил успешное выполнение заказа|has confirmed that order) #(?P<order_id>[A-Z0-9]{8}) '

    r'(?:и отправил деньги продавцу|has been fulfilled successfully and that the seller) (?P<seller>[a-zA-Z0-9]+)(?: has been paid)?\.'
)
'''
Скомпилированное регулярное выражение, описывающее сообщение о подтверждении выполнения заказа.

Доступные группы match: `buyer`, `order_id`, `seller`.
'''


NEW_FEEDBACK_RE = re.compile(
    r'(?:Покупатель|The buyer) (?P<buyer>[a-zA-Z0-9]+) '

    r'(?:написал отзыв к заказу|has given feedback to the order) #(?P<order_id>[A-Z0-9]{8})\.'
)
'''
Скомпилированное регулярное выражение, описывающее сообщение о новом отзыве.

Доступные группы match: `buyer`, `order_id`.
'''


FEEDBACK_CHANGED_RE = re.compile(
    r'(?:Покупатель|The buyer) (?P<buyer>[a-zA-Z0-9]+) '

    r'(?:изменил отзыв к заказу|has edited their feedback to the order) #(?P<order_id>[A-Z0-9]{8})\.'
)


'''
Скомпилированное регулярное выражение, описывающее сообщение об изменении отзыва.

Доступные группы match: `buyer`, `order_id`.
'''


FEEDBACK_DELETED_RE = re.compile(
    r'(?:Покупатель|The buyer) (?P<buyer>[a-zA-Z0-9]+) '

    r'(?:удалил отзыв к заказу|has deleted their feedback to the order) #(?P<order_id>[A-Z0-9]{8})\.')
'''
Скомпилированное регулярное выражение, описывающее сообщение об удалении отзыва.

Доступные группы match: `buyer`, `order_id`.
'''


NEW_FEEDBACK_ANSWER_RE = re.compile(
    r'(?:Продавец|The seller) (?P<seller>[a-zA-Z0-9]+) '

    r'(?:ответил на отзыв к заказу|has replied to their feedback to the order) #(?P<order_id>[A-Z0-9]{8})\.'
)

'''
Скомпилированное регулярное выражение, описывающее сообщение о новом ответе на отзыв.

Доступные группы match: `seller`, `order_id`.
'''


FEEDBACK_ANSWER_CHANGED_RE = re.compile(
    r'(?:Продавец|The seller) (?P<seller>[a-zA-Z0-9]+) '

    r'(?:изменил ответ на отзыв к заказу|has edited a reply to their feedback to the order) #(?P<order_id>[A-Z0-9]{8})\.'
)
'''
Скомпилированное регулярное выражение, описывающее сообщение об изменении ответа на отзыв.

Доступные группы match: `seller`, `order_id`.
'''


FEEDBACK_ANSWER_DELETED_RE = re.compile(
    r'(?:Продавец|The seller) (?P<seller>[a-zA-Z0-9]+) '

    r'(?:удалил ответ на отзыв к заказу|has deleted a reply to their feedback to the order) #(?P<order_id>[A-Z0-9]{8})\.'
)
'''
Скомпилированное регулярное выражение, описывающее сообщение об удалении ответа на отзыв.

Доступные группы match: `seller`, `order_id`.
'''


ORDER_REOPENED_RE = re.compile(
    r'(?:Заказ|Order) #(?P<order_id>[A-Z0-9]{8}) (?:открыт повторно|has been reopened)\.'
)

'''
Скомпилированное регулярное выражение, описывающее сообщение о повтором открытии заказа.

Доступные группы match: `order_id`.
'''


REFUND_RE = re.compile(
    r'(?:Продавец|The seller) (?P<seller>[a-zA-Z0-9]+) '

    r'(?:вернул деньги покупателю|has refunded the buyer) (?P<buyer>[a-zA-Z0-9]+) '

    r'(?:по заказу|on order) #(?P<order_id>[A-Z0-9]{8})\.'
)

'''
Скомпилированное регулярное выражение, описывающее сообщение о возврате денежных средств.

Доступные группы match: `seller`, `buyer`, `order_id`.
'''


REFUND_BY_ADMIN_RE = re.compile(
    r'(?:Администратор|The administrator) (?P<admin>[a-zA-Z0-9]+) '

    r'(?:вернул деньги покупателю|has refunded the buyer) (?P<buyer>[a-zA-Z0-9]+) '

    r'(?:по заказу|on order) #(?P<order_id>[A-Z0-9]{8})\.'
)
'''
Скомпилированное регулярное выражение, описывающее сообщение о возврате денежных средств администратором.

Доступные группы match: `admin`, `buyer`, `order_id`.
'''


PARTIAL_REFUND_RE = re.compile(
    r'(?:Часть средств по заказу|A part of the funds pertaining to the order) #(?P<order_id>[A-Z0-9]{8}) (?:возвращена покупателю|has been refunded)\.'
)

'''
Скомпилированное регулярное выражение, описывающее сообщение частичном о возврате денежных средств.

Доступные группы match: `order_id`.
'''


ORDER_CONFIRMED_BY_ADMIN_RE = re.compile(
    r'(?:Администратор|The administrator) (?P<admin>[a-zA-Z0-9]+) '

    r'(?:подтвердил успешное выполнение заказа|has confirmed that order) #(?P<order_id>[A-Z0-9]{8}) '

    r'(?:и отправил деньги продавцу|has been fulfilled successfully and that the seller) (?P<seller>[a-zA-Z0-9]+)( has been paid)?\.'
)
'''
Скомпилированное регулярное выражение, описывающее сообщение о подтверждении выполнения заказа администратором.

Доступные группы match: `admin`, `order_id`, `seller`.
'''


DISCORD_RE = re.compile(
    r'(?:You can switch to|Вы можете перейти в) Discord\. '

    r'(?:However, note that friending someone is considered a violation rules|Внимание: общение за пределами сервера FunPay считается нарушением правил)\.'
)
'''
Скомпилированное регулярное выражение о предложении перехода в Discord.
'''


DEAR_VENDORS_RE = re.compile(
    r'(?:Уважаемые продавцы|Dear vendors), '

    r'(?:не доверяйте сообщениям в чате|do not rely on chat messages)! '

    r'(?:'
        r'Перед выполнением заказа всегда проверяйте наличие оплаты в разделе «Мои продажи»|'
        r'''Before you process an order, you should always check whether you've been paid in «My sales» section'''
    r')\.'
)
'''
Скомпилированное регулярное выражение первого сообщения FunPay.
'''


EXCHANGE_RATE_RE = re.compile(
    r'(?:You will receive payment in|Вы начнёте получать оплату в|Ви почнете одержувати оплату в) '

    r'(?P<currency_to>USD|RUB|EUR)\. '

    r'(?:'
        r'Your offers prices will be calculated based on the exchange rate:|'
        r'Цены ваших предложений будут пересчитаны по курсу|'
        r'Ціни ваших пропозицій будуть перераховані за курсом'
    r') '

    r'(?P<exchange_rate_currency_from>[\d.,]+) '
    r'(?P<currency_from_symbol>₽|€|\$) (?:за|for) '

    r'(?P<exchange_rate_currency_to>[\d.,]+) '
    r'(?P<currency_to_symbol>₽|€|\$)\.'
)
'''
Скомпилированное регулярное выражение, описывающее фразу о смене валюты.

Доступные группы match: `currency_to`, `exchange_rate_currency_from`, `currency_from_symbol`, `exchange_rate_currency_to`, `currency_to_symbol`.
'''


FUNPAY_URL_RE = re.compile(
    r'https:\/\/funpay\.com\/'

    r'(?:(?P<locale>en|uk)\/)?'

    r'(?P<api_method>\w+(?:\/\w+)*)?'

    r'(?:\?(?P<query_params>(?:&?[^=&]*=[^=&]*)*))?'

    r'\/?'
)
'''
Скомпилированное регулярное выражение, описывающее полный URL ссылки FunPay.

Доступные группы match: `locale`, `api_method`, `query_params`.
'''


from .types import *


__all__ = [
    'exceptions',
    'generate_random_tag',
    'PRIVATE_CHAT_ID_RE',
    'ORDER_ID_RE',
    'PRODUCTS_AMOUNT_RE',
    'ORDER_PURCHASED_RE',
    'ORDER_CONFIRMED_RE',
    'NEW_FEEDBACK_RE',
    'FEEDBACK_CHANGED_RE',
    'FEEDBACK_DELETED_RE',
    'NEW_FEEDBACK_ANSWER_RE',
    'FEEDBACK_ANSWER_CHANGED_RE',
    'FEEDBACK_ANSWER_DELETED_RE',
    'ORDER_REOPENED_RE',
    'REFUND_RE',
    'REFUND_BY_ADMIN_RE',
    'PARTIAL_REFUND_RE',
    'ORDER_CONFIRMED_BY_ADMIN_RE',
    'DISCORD_RE',
    'DEAR_VENDORS_RE',
    'EXCHANGE_RATE_RE',
    'FUNPAY_URL_RE',
    'EventTypes',
    'MessageTypes',
    'OrderStatuses',
    'SubCategoryTypes',
    'Currencies',
    'Wallets',
    'Months',
    'FloodErrorTexts',
    'MultiuserFloodErrorTexts',
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