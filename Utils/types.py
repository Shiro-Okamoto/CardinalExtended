'В этом модуле описаны различные типы, датаклассы и перечисления Кардинала.'
from __future__ import annotations


from . import exceptions


from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Callable, Literal, Any, NoReturn
from abc import ABC, abstractmethod
from time import sleep, time


from typing import TYPE_CHECKING
if TYPE_CHECKING: from cardinal import Cardinal


# ---------------------------------------------------------------------------- #
#                                  Датаклассы                                  #
# ---------------------------------------------------------------------------- #
@dataclass
class Plugin:
    'Класс, описывающий плагин Кардинала.'
    uuid: str
    name: str
    version: str
    description: str
    credits: str
    dir: Path
    dependencies: dict
    raw_info: dict
    module: ModuleType | None = None
    handlers: dict[
        Literal[
            'PRE_INIT',
            'POST_INIT',
            'PRE_START',
            'POST_START',
            'PRE_STOP',
            'POST_STOP',
            'INIT_MESSAGE',
            'MESSAGES_LIST_CHANGED',
            'LAST_CHAT_MESSAGE_CHANGED',
            'NEW_MESSAGE',
            'INIT_ORDER',
            'NEW_ORDER',
            'ORDERS_LIST_CHANGED',
            'ORDER_STATUS_CHANGED',
            'PROFILE_UPDATE'
        ] | str,
        list[Handler]
    ] = field(default_factory=dict)


@dataclass
class Handler:
    'Класс, описывающий хендлер Кардинала.'
    plugin_uuid: str
    type: Literal[
        'PRE_INIT',
        'POST_INIT',
        'PRE_START',
        'POST_START',
        'PRE_STOP',
        'POST_STOP',
        'INIT_MESSAGE',
        'MESSAGES_LIST_CHANGED',
        'LAST_CHAT_MESSAGE_CHANGED',
        'NEW_MESSAGE',
        'INIT_ORDER',
        'NEW_ORDER',
        'ORDERS_LIST_CHANGED',
        'ORDER_STATUS_CHANGED',
        'PROFILE_UPDATE'
    ] | str
    priority: int
    func: Callable[..., None]


@dataclass
class Tag:
    '''
    Класс, описывающий тег GitHub.
    '''
    json: dict[str, Any] = field(default_factory=dict)


    @property
    def name(self) -> str: return self.json['name']

    @property
    def zipball_url(self) -> str: return self.json['zipball_url']

    @property
    def tarball_url(self) -> str: return self.json['tarball_url']

    @property
    def commit_url(self) -> str: return self.json['commit']['url']

    @property
    def node_id(self) -> str: return self.json['node_id']


@dataclass
class Release:
    '''
    Класс, описывающий релиз GitHub.
    '''
    json: dict[str, Any] = field(default_factory=dict)


    @property
    def id(self) -> int: return self.json['id']

    @property
    def name(self) -> str: return self.json['name']

    @property
    def tag_name(self) -> str: return self.json['tag_name']

    @property
    def url(self) -> str: return self.json['url']

    @property
    def html_url(self) -> str: return self.json['html_url']

    @property
    def target_commitish(self) -> str: return self.json['target_commitish']

    @property
    def draft(self) -> bool: return self.json['draft']

    @property
    def prerelease(self) -> bool: return self.json['prerelease']

    @property
    def created_at(self) -> str: return self.json['created_at']

    @property
    def updated_at(self) -> str: return self.json['updated_at']

    @property
    def published_at(self) -> str: return self.json['published_at']


    @property
    def tarball_url(self) -> str: return self.json['tarball_url']

    @property
    def zipball_url(self) -> str: return self.json['zipball_url']

    @property
    def body(self) -> str: return self.json['body']

    @property
    def author_id(self) -> int: return self.json['author']['id']

    @property
    def author(self) -> str: return self.json['author']['login']

    @property
    def assets_url(self) -> str: return self.json['assets_url']

    @property
    def upload_url(self) -> str: return self.json['upload_url']

    @property
    def assets(self) -> list: return self.json['assets']


# ---------------------------------------------------------------------------- #
#                                    Классы                                    #
# ---------------------------------------------------------------------------- #
class CardinalWorker:
    def __init__(
            self,
            crd: Cardinal,
            foo: Callable[..., float | None],
            running_flag_name: str | None = None,
            foo_result_is_work_delay: bool = False, work_delay: float = 1,
            foo_args: tuple | None = None, foo_kwargs: dict | None = None
    ):
        '''
        Класс-декоратор для бесконечных циклов Кардинала.

        :param crd: Связанный экземпляр Кардинала.
        :type crd: Cardinal
        :param foo: Рабочая функция.
        :type foo: Callable[..., float  |  None]
        :param running_flag_name: Имя атрибута Кардинала - флага запущенного бесконечного цикла, defaults to None.
        :type running_flag_name: str | None, опционально
        :param foo_result_is_work_delay: Использовать результат рабочей функции, как задержку после вызова, defaults to False.
        :type foo_result_is_work_delay: bool, опционально
        :param work_delay: Задержка после вызова рабочей функции, defaults to 1.
        :type work_delay: float, опционально
        '''
        self.__crd = crd
        'Связанный экземпляр Кардинала.'
        self.__foo = foo
        'Рабочая функция.'
        self.args: tuple[Any] = foo_args or tuple()
        'Аргументы для рабочей функции.'
        self.kwargs: dict[str, Any] = foo_kwargs or {}
        'Именованные аргументы для рабочей функции.'
        self.delay = work_delay
        'Задержка после вызова рабочей функции.'
        self.__foo_result_is_work_delay = foo_result_is_work_delay
        'Использовать результат рабочей функции, как задержку после вызова.'


        self.__running_flag_name = running_flag_name
        'Имя атрибута Кардинала - флага запущенного бесконечного цикла.'

        if self.__running_flag_name: setattr(self.__crd, self.__running_flag_name, False)


        self.__running = False
        'Флаг запущенного бесконечного цикла.'

        self.__stopping = False
        'Флаг остановки бесконечного цикла.'


    @property
    def foo(self) -> Callable[..., float | None]:
        '''
        Рабочая функция.
        '''
        return self.__foo


    @property
    def running(self) -> bool:
        '''
        Запущен ли бесконечный цикл.
        '''
        if self.__running_flag_name: return getattr(self.__crd, self.__running_flag_name)


        return self.__running


    @running.setter
    def running(self, value: bool) -> None:
        if self.__running_flag_name: setattr(self.__crd, self.__running_flag_name, value)

        else: self.__running = value


        return


    @property
    def stopped(self) -> bool:
        '''
        Остановлен ли бесконечный цикл.
        '''
        return not self.running


    def work(self, *args, **kwargs) -> float | None:
        '''
        Выполняет рабочую функцию один раз с указанными аргументами.
        '''
        return self.foo(*args, **kwargs)


    def run(self) -> NoReturn:
        '''
        Бесконечно вызывает рабочую функцию.

        :raises exceptions.CardinalWorkerRunningError: Бесконечный цикл уже запущен.
        '''
        if self.running: raise exceptions.CardinalWorkerRunningError()


        self.running = True

        next_work_time = time()

        while True:
            sleep(.1)

            if self.__stopping:
                self.running = False


                return


            if next_work_time <= time():
                result = self.work(*self.args, **self.kwargs)


                delay = result if self.__foo_result_is_work_delay else self.delay

                next_work_time = time() + (delay or self.delay)


    def stop(self) -> None:
        '''
        Останавливает бесконечный цикл.
        '''
        self.__stopping = True


        return


    def wait_until_stopped(self, check_delay: float = .5) -> None:
        '''
        Блокирующая функция, ожидающая, когда бесконечный цикл остановится.

        :param check_delay: Задержка между проверками, defaults to 0.5.
        :type check_delay: float, опционально
        '''
        while True:
            if self.stopped: return


            sleep(check_delay)


# ---------------------------------------------------------------------------- #
#                              Абстрактные классы                              #
# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
#                             Перечисления (Enums)                             #
# ---------------------------------------------------------------------------- #


__all__ = [
    'Plugin',
    'Handler',
    'Tag',
    'Release',
    'CardinalWorker'
]