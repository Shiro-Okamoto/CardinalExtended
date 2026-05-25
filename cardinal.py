'Здесь описан класс Кардинала.'
from __future__ import annotations


from subprocess import Popen
import importlib.util


from Utils import (
    ENTITY_RE, exceptions, check_proxy, set_console_title, Plugin, Handler, get_new_releases, get_current_cardinal_version, download_release, extract_release,
    install_release, CardinalWorker
)


from configs import Config, HOME_DIR


from FunPayAPI import Account, Runner, EventTypes, SubCategoryTypes, Currencies, Message, LotShortcut, UserProfile, Balance, exceptions as fpapi_exceptions


import json
import hashlib
from _hashlib import HASH as Hash
from types import ModuleType
from typing import Literal, Any, NoReturn
from pathlib import Path
from datetime import datetime
import logging
import random
from time import time, sleep
from math import inf


from localizer import Localizer


from threading import Thread


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from importlib._bootstrap import ModuleSpec

    from Utils import Release


log = logging.getLogger('C_EXT')


def get_cardinal(name: str = 'Cardinal') -> None | Cardinal:
    '''
    Возвращает существующий экземпляр Кардинала.
    '''
    return Cardinal.instances.get(name)


class Cardinal:
    instances = {}
    'Список существующих экземпляров Кардинала.'


    def __new__(cls, name: str, *args, **kwargs):
        if not name in cls.instances: cls.instances[name] = super().__new__(cls)

        return cls.instances[name]


    def __init__(self, name: str, version: str):
        if hasattr(self, '__initiated'): return

        self.__initiated = True

        self.name = name
        'Имя экземпляра.'

        self.version = version


        self.run_id = 0

        self.initiated = False
        'Флаг инициализации Кардинала.'

        self.process_events_loop_running = False
        'Флаг запущенного обработчика событий.'
        self.update_session_loop_running = False
        'Флаг запущенного цикла обновления данных о пользователе.'
        self.check_cardinal_updates_loop_running = False
        'Флаг запущенного цикла проверки обновлений Кардинала.'


        self.start_time = int(time())


        if self.config.proxy.enable: self.__init_proxy()
        else: self.proxy = {}


        self.account = Account(
            self.config.FunPay.golden_key,
            self.config.FunPay.user_agent,
            proxy=self.proxy
        )

        self.runner: Runner | None = None
        'Runner.'

        self.profile: UserProfile | None = None
        'Профиль FunPay'

        self.balance: Balance | None = None
        'Баланс аккаунта FunPay.'


        self.lot_shortcuts: list[LotShortcut] = []
        'Список всех лотов профиля FunPay.'

        self.lot_ids: list[int | str] = []
        'Айди лотов профиля FunPay.'


        self.__exchange_rates = {}
        'Курс валют {(валюта1, валюта2): (курс, время обновления)}'


        self.session_update_worker: CardinalWorker = None
        'Обработчик обновления сессии.'
        self.session_update_worker_running: bool = False
        'Флаг запущенного бесконечного цикла обновления сессии.'


        self.check_updates_worker: CardinalWorker = None
        'Обработчик проверки обновлений Кардинала.'
        self.check_updates_worker_running: bool = False
        'Флаг запущенного бесконечного цикла проверки обновлений Кардинала.'


        self.event_var_names = [
            'PRE_INIT', # Функции, выполняемые до инициализации Кардинала (после загрузки плагинов).
            'POST_INIT', # Функции, выполняемые после инициализации Кардинала.
            'PRE_START', # Функции, выполняемые перед запуском Кардинала (выполняются первыми).
            'POST_START', # Функции, выполняемые перед запуском Кардинала (после PRE_START).
            'PRE_STOP', # Функции, выполняемые при остановке Кардинала (выполняются первыми).
            'POST_STOP', # Функции, выполняемые при остановке Кардинала (после PRE_STOP).
            'INITIAL_CHAT', # Функции, выполняемые при получении чата при запуске раннера.
            'CHATS_LIST_CHANGED', # Функции, выполняемые при изменении списка чатов или последнего сообщения любого из чатов.
            'LAST_CHAT_MESSAGE_CHANGED', # Функции, выполняемые при изменении последнего сообщения в чате.
            'NEW_MESSAGE', # Функции, выполняемые при получении нового сообщения.
            'INITIAL_ORDER', # Функции, выполняемые при обнаружении заказа при запуске раннера.
            'NEW_ORDER', # Функции, выполняемые при получении нового заказа.
            'ORDERS_LIST_CHANGED', # Функции, выполняемые при изменении списка заказов или их статусов.
            'ORDER_STATUS_CHANGED', # Функции, выполняемые при изменении статуса заказа.
            'PROFILE_UPDATE_SUCCESS', # Функции, выполняемые при успешном обновлении профиля.
            'HANDLER_ERROR', # Функции, выполняемые при ошибке выполнения хендлера (могут вызвать бесконечную рекурсию).
            'SESSION_UPDATE_SUCCESS', # Функции, выполняемые при успешном обновлении сессии.
            'SESSION_UPDATE_ERROR,' # Функции, выполняемые при ошибке обновления сессии.
            'GET_BALANCE_SUCCESS', # Функции, выполняемые при успешном получении баланса аккаунта.
            'PRE_INIT_ACCOUNT', # Функции, выполняемые перед инициализацией (получением) аккаунта.
            'POST_INIT_ACCOUNT', # Функции, выполняемые после инициализации (получения) аккаунта и баланса.
            'NEW_PRE_RELEASE_VERSION_AVAILABLE', # Функции, выполняемые, когда Кардинал находит новую пре-релизную версию, но авто-загрузка отключена.
            'NEW_VERSION_AVAILABLE', # Функции, выполняемые, когда Кардинал находит новую версию, но авто-загрузка отключена.
            'PRE_UPDATE', # Функции, выполняемые перед началом обновления программы.
            'UPDATE_ERROR', # Функции, выполняемые в случае ошибки обновления.
            'POST_UPDATE', # Функции, выполняемые после обновления программы.
            'PRE_DOWNLOAD_RELEASE', # Функции, выполняемые перед скачиванием обновления.
            'POST_DOWNLOAD_RELEASE', # Функции, выполняемые после скачивания обновления.
            'PRE_INSTALL_RELEASE', # Функции, выполняемые перед установкой обновления.
            'POST_INSTALL_RELEASE', # Функции, выполняемые после успешной установки обновления.
        ]
        'Имена событий для привязки хендлеров.'

        self.handlers: dict[Literal[
            'PRE_INIT',
            'POST_INIT',
            'PRE_START',
            'POST_START',
            'PRE_STOP',
            'POST_STOP',
            'INITIAL_CHAT',
            'CHATS_LIST_CHANGED',
            'LAST_CHAT_MESSAGE_CHANGED',
            'NEW_MESSAGE',
            'INITIAL_ORDER',
            'NEW_ORDER',
            'ORDERS_LIST_CHANGED',
            'ORDER_STATUS_CHANGED',
            'PROFILE_UPDATE_SUCCESS',
            'HANDLER_ERROR',
            'SESSION_UPDATE_SUCCESS',
            'SESSION_UPDATE_ERROR',
            'GET_BALANCE_SUCCESS',
            'PRE_INIT_ACCOUNT',
            'POST_INIT_ACCOUNT',
            'NEW_PRE_RELEASE_VERSION_AVAILABLE',
            'NEW_VERSION_AVAILABLE',
            'PRE_UPDATE',
            'UPDATE_ERROR',
            'POST_UPDATE',
            'PRE_DOWNLOAD_RELEASE',
            'POST_DOWNLOAD_RELEASE',
            'PRE_INSTALL_RELEASE',
            'POST_INSTALL_RELEASE',
        ] | str, list[Handler]] = {}
        'Список загруженных хендлеров.'


        self.plugins_load_order: list[str] = []
        'Порядок загрузки плагинов.'

        self.plugins: dict[str, Plugin] = {}
        'Список загруженных плагинов.'


    def __init_proxy(self) -> None:
        if self.config.proxy.ip and self.config.proxy.port.isnumeric():
            log.info(self.translate('c_ext_proxy_detected'))

            ip = self.config.proxy.ip
            port = self.config.proxy.port

            login = self.config.proxy.login
            password = self.config.proxy.password

            proxy_str = (f'{login}:{password}@' if login and password  else '') + f'{ip}:{port}'

            self.proxy = {
                'http': f'http://{proxy_str}',
                'https': f'http://{proxy_str}'
            }


            if self.config.proxy.check:
                log.info(self.translate('c_ext_checking_proxy'))

                try: response = check_proxy(self.proxy)

                except:
                    log.error(self.translate('c_ext_proxy_err'))
                    log.debug('TRACEBACK', exc_info=True)


                    return


            log.info(self.translate('c_ext_proxy_success', response.content.decode()))


        return


    # ---------------------------------------------------------------------------- #
    #                             Управление процессом                             #
    # ---------------------------------------------------------------------------- #
    def init(self):
        '''
        Инициализирует Кардинал.

        Загружает плагины, регистрирует хэндлеры, получает данные аккаунта и профиля.
        '''
        log.info(self.translate('c_ext_initializing_cardinal'))


        self.get_plugins()
        self.load_plugins()
        self.init_plugins()
        self.add_handlers_from_plugins()


        self.run_handlers(self.handlers.get('PRE_INIT', []))


        self.__init_account()

        self.runner = Runner(self.account, self.config.FunPay.oldMsgGetMode)

        self.__update_profile()


        self.session_update_worker = CardinalWorker(
            self,
            self.update_session,
            'session_update_worker_running',
            True,
            60,
            (3,)
        )

        self.session_update_worker_running: bool = False


        self.check_updates_worker = CardinalWorker(
            self,
            self.__check_updates,
            'check_updates_worker_running',
            True,
            60
        )

        self.check_updates_worker_running: bool = False


        self.run_handlers(self.handlers.get('POST_INIT', []))


        self.initiated = True

        return self


    def start(self):
        '''
        Запускает Кардинал.

        :raises CardinalNotInitializedException: Кардинал не был инициализирован перед запуском.
        '''
        log.info(self.translate('c_ext_starting_cardinal'))

        if not self.initiated: raise exceptions.CardinalNotInitializedError()


        self.start_time = int(time())

        self.run_id += 1


        self.run_handlers(self.handlers.get('PRE_START', []))

        self.run_handlers(self.handlers.get('POST_START', []))


        Thread(target=self.session_update_worker.run, daemon=True).start()
        Thread(target=self.check_updates_worker.run, daemon=True).start()


        self.process_events()


    def stop(self):
        '''
        Останавливает Кардинал.
        '''
        log.info(self.translate('c_ext_stopping_cardinal'))

        self.run_handlers(self.handlers.get('PRE_STOP', []))


        self.session_update_worker.stop()
        self.check_updates_worker.stop()

        self.run_id += 1


        self.run_handlers(self.handlers.get('POST_STOP', []))


    def full_stop(self) -> NoReturn:
        '''
        Полностью останавливает программу.
        '''
        self.stop()

        exit('Запланированное закрытие программы')


    def full_reload(self) -> NoReturn:
        '''
        Полностью перезапускает программу.
        '''
        Popen(str(HOME_DIR / 'main.py'), shell=True)

        self.full_stop()


    def update_session(self, attempts: int = 3) -> Literal[60, 3600]:
        '''
        Обновляет данные аккаунта (баланс, токены и т.д.)

        :param attempts: Кол-во попыток, defaults to 3.
        :type attempts: int, опционально
        :return: Время (в секундах) для следующего вызова (в бесконечном цикле): 60, если не удалось получить данные аккаунта, иначе 3600.
        :rtype: int
        '''
        log.info(self.translate('c_ext_updating_session'))

        for _ in range(attempts):
            try:
                self.account.get(update_phpsessid=True)


                log.info(self.translate('c_ext_session_updated'))

                self.run_handlers(self.handlers.get('SESSION_UPDATE_SUCCESS', []))


                return 60*60


            except TimeoutError: log.warning(self.translate('c_ext_session_timeout_err'))

            except fpapi_exceptions.UnauthorizedError as err:
                log.error(self.translate('c_ext_unauthorized_error_short_str'))
                log.debug(
                    self.translate(
                        'c_ext_request_failed_error',
                        err.url, err.response.request.method, err.status_code, err.request_headers, err.request_body, err.response.text
                    )
                )

            except fpapi_exceptions.RequestFailedError as err:
                log.error(self.translate('c_ext_request_failed_error_short_str', err.url, err.status_code))
                log.debug(
                    self.translate(
                        'c_ext_request_failed_error',
                        err.url, err.response.request.method, err.status_code, err.request_headers, err.request_body, err.response.text
                    )
                )

            except:
                log.error(self.translate('c_ext_session_unexpected_err'))
                log.debug('TRACEBACK', exc_info=True)


            log.warning(self.translate('c_ext_try_again_in_n_secs', 2))


            sleep(2)

            continue


        else:
            log.error(self.translate('c_ext_session_no_more_attempts_err'))

            return 60


    def __init_account(self) -> None:
        '''
        Инициализирует аккаунт.
        '''
        log.info(self.translate('c_ext_getting_acc'))

        self.run_handlers(self.handlers.get('PRE_INIT_ACCOUNT', []))


        while True:
            try:
                self.account.get()
                self.balance = self.get_balance()


                set_console_title(f'FunPay Cardinal - {self.account.username} ({self.account.id})')


                greeting_text = self.__create_greeting_text()
                for line in greeting_text.split('\n'): log.info(line)


                break

            except TimeoutError: log.error(self.translate('c_ext_acc_get_timeout_err'))

            except fpapi_exceptions.UnauthorizedError as err:
                log.error(self.translate('c_ext_unauthorized_error_short_str'))
                log.debug(
                    self.translate(
                        'c_ext_request_failed_error',
                        err.url, err.response.request.method, err.status_code, err.request_headers, err.request_body, err.response.text
                    )
                )

            except fpapi_exceptions.RequestFailedError as err:
                log.error(self.translate('c_ext_request_failed_error_short_str', err.url, err.status_code))
                log.debug(
                    self.translate(
                        'c_ext_request_failed_error',
                        err.url, err.response.request.method, err.status_code, err.request_headers, err.request_body, err.response.text
                    )
                )

            except exceptions.GetBalanceError: log.error(self.translate('c_ext_acc_get_balance_get_error'))

            except:
                log.error(self.translate('c_ext_acc_get_unexpected_err'))
                log.debug('TRACEBACK', exc_info=True)


            log.warning(self.translate('c_ext_try_again_in_n_secs', 2))

            sleep(2)


        self.run_handlers(self.handlers.get('POST_INIT_ACCOUNT', []))


        return


    def __update_profile(self, infinite_polling: bool = True, attempts: int = 3) -> None:
        '''
        Обновляет профиль FunPay.

        :param infinite_polling: Бесконечно посылать запросы, пока не будет получен ответ (игнорировать макс. кол-во попыток), defaults to True.
        :type infinite_polling: bool, опционально
        :param attempts: Максимальное кол-во попыток, defaults to 3.
        :type attempts: int, опционально
        :raises exceptions.ProfileUpdateError: Не удалось обновить профиль.
        '''
        log.info(self.translate('c_ext_getting_profile_data'))


        _ = attempts

        while _ or infinite_polling:
            try:
                self.profile = self.account.get_user(self.account.id)
                break

            except TimeoutError: log.error(self.translate('c_ext_profile_get_timeout_err'))

            except fpapi_exceptions.RequestFailedError as e:
                log.error(e.short_str())
                log.debug(e)

            except:
                log.error(self.translate('c_ext_profile_get_unexpected_err'))
                log.debug('TRACEBACK', exc_info=True)


            _-=1

            log.warning(self.translate('c_ext_try_again_in_n_secs', 2))

            sleep(2)


        else:
            log.error(self.translate('c_ext_profile_get_too_many_attempts_err', attempts))

            raise exceptions.ProfileUpdateError()


        self.lot_shortcuts = self.profile.lots
        self.lot_ids = [i.id for i in self.lot_shortcuts]
        log.info(self.translate('c_ext_profile_updated', len(self.lot_shortcuts), len(self.profile.sorted_by_subcategory_lots)))


        self.run_handlers(self.handlers.get('PROFILE_UPDATE_SUCCESS', []))


        return


    def process_events(self) -> NoReturn:
        '''
        Бесконечно получает события FunPay и запускает связанные хендлеры.
        '''
        log.info(self.translate('c_ext_starting_process_events_loop'))

        self.process_events_loop_running = True

        instance_id = self.run_id


        event_handlers = {
            event_type: event_type.name for event_type in EventTypes
        }


        try:
            for event in self.runner.listen(requests_delay=int(self.config.Other.requestsDelay)):
                if instance_id != self.run_id:
                    self.process_events_loop_running = False

                    break


                self.run_handlers(self.handlers.get(event_handlers[event.type], []), event)


        except StopIteration: return


    # ---------------------------------------------------------------------------- #
    #                                  Обновления                                  #
    # ---------------------------------------------------------------------------- #
    def __check_updates(self) -> int | Literal[60]:
        '''
        Проверяет наличие обновлений. Автоматически обновляет и перезапускает Кардинал, если включены соответствующие настройки.

        :return: Задержка (в секундах) для следующей проверки обновлений (для бесконечного цикла). 60 при ошибке, иначе значение из конфига.
        :rtype: int
        '''
        try:
            # ----------------------- Проверяем наличие обновлений ----------------------- #
            releases = self.check_updates()

            # ------------------------ Если найдены новые релизы, ------------------------ #
            if releases:
                # ---------------------- но авто-обновление выключено - ---------------------- #
                if not self.config.auto_update:
                    # --------------- отправляем уведомления о наличии новых версий -------------- #
                    for release in releases:
                        if release.prerelease:
                            log.info(self.translate('c_ext_new_prerelease_version_available', release.tag_name))

                            self.run_handlers(self.handlers.get('NEW_PRE_RELEASE_VERSION_AVAILABLE', []), [release])


                            continue

                        log.info(self.translate('c_ext_new_version_available', release.tag_name))

                        self.run_handlers(self.handlers.get('NEW_VERSION_AVAILABLE', []), [release])


                    return self.config.check_for_updates_delay


                release = releases[0]

                # --------- это не пре-релиз или включено обновление до пре-релиза - --------- #
                if any([
                    not release.prerelease,
                    self.config.install_prereleases
                ]):
                    # ---------------------------- обновляем Кардинал ---------------------------- #
                    self.update(release)


                    return self.config.check_for_updates_delay


                # --------- но это пре-релиз, а обновление до пре-релиза выключено - --------- #
                # ---------------- отправляем уведомление о наличии пре-релиза --------------- #
                log.info(self.translate('c_ext_new_prerelease_version_available', release.tag_name))

                self.run_handlers(self.handlers.get('NEW_PRE_RELEASE_VERSION_AVAILABLE', []), [release])


                return self.config.check_for_updates_delay


            # ----------------------------- Если релизов нет ----------------------------- #
            return self.config.check_for_updates_delay


        except SystemExit: exit('Запланированное закрытие программы')


        # ---------- Ошибка при обновлении - повторяем попытку через минуту ---------- #
        except:
            log.warning(self.translate('c_ext_check_updates_error'))
            log.debug('TRACEBACK', exc_info=True)


            log.warning(self.translate('c_ext_try_again_in_n_secs', 60))


            return 60


    def check_updates(self) -> list[Release] | None:
        '''
        Проверяет наличие обновлений программы.

        :raises Exception: В конфиге отсутствует ссылка на GitHub.
        :return: Список релизов.
        :rtype: list[Release] | None
        '''
        log.debug(self.translate('c_ext_checking_updates'))

        if not self.config.github_api_page_url: raise exceptions.GitHubAPIUrlNotSpecified()


        releases = get_new_releases(get_current_cardinal_version(), self.config.github_api_page_url)


        return releases


    def update(self, release: Release) -> NoReturn: # TODO Варианты действий в зависимости от ошибки
        '''
        Обновляет и полностью перезапускает Кардинал.

        :param release: Информация об обновлении.
        :type release: Release
        '''
        log.info(self.translate('c_ext_starting_update'))

        self.run_handlers(self.handlers.get('PRE_UPDATE', []), [release])


        try:
            folder_name = self.__download_release(release)

            self.__install_release(folder_name)


        except Exception as err:
            log.error(self.translate('c_ext_update_error'))

            self.run_handlers(self.handlers.get('UPDATE_ERROR', []), [release, err])


            return


        self.run_handlers(self.handlers.get('POST_UPDATE', []), [release])


        self.full_reload()


    def __download_release(self, release: Release) -> str:
        '''
        Скачивает и распаковывает обновление.

        :param release: Релиз.
        :type release: Release
        :return: Имя папки скачанного релиза
        :rtype: str
        '''
        log.info(self.translate('c_ext_downloading_release', release.tag_name))

        self.run_handlers(self.handlers.get('PRE_DOWNLOAD_RELEASE', []), [release])


        download_release(release)

        folder_name = extract_release()


        self.run_handlers(self.handlers.get('POST_DOWNLOAD_RELEASE', []), [release])


        return folder_name


    def __install_release(self, folder_name: str) -> None:
        '''
        Устанавливает обновление.

        :param folder_name: Имя папки с обновлением.
        :type folder_name: str
        :raises InstallUpdateError: Не удалось установить обновление.
        '''
        log.info(self.translate('c_ext_installing_release', folder_name))

        self.run_handlers(self.handlers.get('PRE_INSTALL_RELEASE', []))

        try: install_release(folder_name)


        except: raise exceptions.InstallUpdateError()


        self.run_handlers(self.handlers.get('POST_INSTALL_RELEASE', []))


        return


    # ---------------------------------------------------------------------------- #
    #                                    Плагины                                   #
    # ---------------------------------------------------------------------------- #

    # ----------------------------- Загрузка плагинов ---------------------------- #
    def get_plugins(self) -> None:
        'Получает все плагины из папки plugins. Не импортирует модули.'
        log.debug(self.translate('c_ext_getting_plugins'))

        plugins_count = 0
        plugin_dirs = (Path(__file__).parent / 'plugins').iterdir()

        for plugin_dir in plugin_dirs:
            # ---------- Если нет plugin_info.json или plugin.py - это не плагин --------- #
            if not all([
                (plugin_dir / 'plugin.py').exists(),
                (plugin_dir / 'plugin_info.json').exists()
            ]): continue

            plugin_uuid, plugin_raw_info = self.get_plugin_raw_info(plugin_dir)

            plugin = Plugin(
                uuid=plugin_uuid,
                name=plugin_raw_info['NAME'],
                version=plugin_raw_info['VERSION'],
                description=plugin_raw_info['DESCRIPTION'],
                credits=plugin_raw_info['CREDITS'],
                dir=plugin_dir,
                dependencies=plugin_raw_info['dependencies'],
                raw_info=plugin_raw_info
            )

            self.plugins[plugin.uuid] = plugin
            plugins_count+=1

        log.debug(self.translate('c_ext_getting_plugins_success', plugins_count))

        return


    @staticmethod
    def get_plugin_raw_info(plugin_dir: Path) -> tuple[str, dict[str, Any]]:
        '''
        Возвращает информацию о плагине.

        :param plugin_dir: Путь к плагину.
        :type plugin_dir: Path
        :return: Информация о плагине.
        :rtype: dict[str, Any]
        '''
        log.debug(f'c_ext_getting_plugin_raw_info', plugin_dir)

        plugin_info_path = plugin_dir / 'plugin_info.json'
        plugin_dependencies_path = plugin_dir / 'dependencies.json'
        with open(plugin_info_path, encoding='utf-8') as fp: plugin_info = json.load(fp)

        if plugin_dependencies_path.exists():
            with open(plugin_dependencies_path, encoding='utf-8') as fp: plugin_dependencies = json.load(fp)
        else: plugin_dependencies = {}

        plugin_hash = Cardinal.get_plugin_hash(plugin_dir)

        return plugin_info['UUID'], {
            'NAME': plugin_info['NAME'],
            'VERSION': plugin_info['VERSION'],
            'DESCRIPTION': plugin_info['DESCRIPTION'],
            'CREDITS': plugin_info['CREDITS'],
            'dependencies': plugin_dependencies,
            'plugin_dir': plugin_dir,
            'plugin_hash': plugin_hash
        }


    @staticmethod
    def get_plugin_hash(plugin_dir: Path) -> Hash:
        '''
        Возвращает sha256 хеш плагина.

        :param plugin_dir: Путь к плагину.
        :type plugin_dir: Path
        :return: Хеш файлов плагина.
        :rtype: dict[str, HASH]
        '''
        def hash_update_from_file(file_path: Path, hash: Hash):
            hash.update(file_path.read_bytes())


            return hash

        def hash_update_from_dir(directory: Path, hash: Hash):
            for path in sorted(directory.iterdir(), key=lambda p: str(p).lower()):
                if '__pycache__' in str(directory): continue

                hash.update(path.name.encode())


                if path.is_file(): hash = hash_update_from_file(path, hash)

                elif path.is_dir(): hash = hash_update_from_dir(path, hash)


            return hash


        log.debug(f'c_ext_getting_plugin_hash', plugin_dir)

        result = hashlib.sha256()

        result = hash_update_from_dir(plugin_dir, result)


        return result


    def load_plugins(self) -> None:
        'Загружает плагины, полученные через get_plugins.'
        log.debug(self.translate('c_ext_loading_plugins'))

        plugins_raw_info = {plugin.uuid: plugin.raw_info for plugin in self.plugins.values()}

        plugins_raw_info = self.set_plugins_load_order(plugins_raw_info)

        self.get_plugins_load_order(plugins_raw_info)

        plugins_count = 0

        for plugin_uuid in self.plugins_load_order:
            try:
                self.load_plugin(plugin_uuid)

                plugins_count+=1

            except exceptions.PluginNotTrustedException:
                log.warning(self.translate('c_ext_plugin_is_not_trusted_err', plugin_uuid))

                del self.plugins[plugin_uuid]

            except exceptions.PluginDependenciesNotLoadedError:
                log.error(self.translate('c_ext_plugin_dependencies_not_loaded_err', plugin_uuid))
                log.debug('TRACEBACK', exc_info=True)

                del self.plugins[plugin_uuid]

            except:
                log.error(self.translate('c_ext_plugin_load_error', plugin_uuid))
                log.debug('TRACEBACK', exc_info=True)

                del self.plugins[plugin_uuid]


        log.debug(self.translate('c_ext_loading_plugins_success', plugins_count))

        return


    @staticmethod
    def set_plugins_load_order(plugins_raw_info: dict[str, dict]) -> dict[str, dict]:
        '''
        Присваивает плагинам порядок загрузки.

        :param plugins_raw_info: Список плагинов.
        :type plugins_raw_info: dict
        :return: Список плагинов с порядком загрузки.
        :rtype: dict
        '''
        result = plugins_raw_info.copy()

        for plugin_uuid in plugins_raw_info:
            result = Cardinal.set_plugin_load_order(plugin_uuid, result)


        return result


    @staticmethod
    def set_plugin_load_order(plugin_uuid: str, plugins_raw_info: dict[str, dict]) -> dict[str, dict]:
        '''
        Присваивает плагину порядок загрузки, исходя из его зависимостей.

        :param plugin_uuid: UUID плагина.
        :type plugin_uuid: str
        :param plugins_raw_info: Список плагинов
        :type plugins_raw_info: dict
        :return: Список плагинов.
        :rtype: dict
        '''
        plugin_raw_info = plugins_raw_info[plugin_uuid]

        # ---------- Если плагину уже присвоен порядок загрузки - пропустить --------- #
        if hasattr(plugin_raw_info, 'load_order'):
            return plugins_raw_info

        # ------------ Если у плагина нет зависимостей - загружать первым ------------ #
        if not plugin_raw_info['dependencies']:
            plugin_raw_info['load_order'] = 0
            plugins_raw_info[plugin_uuid] = plugin_raw_info

        # ----- Если у плагина есть зависимости - присвоить каждой из них порядок ---- #
        # ------------------ загрузки, а плагин загрузить после них ------------------ #
        else:
            load_order = 0

            for dependency in plugin_raw_info['dependencies']:
                if not hasattr(plugins_raw_info[dependency], 'load_order'): plugins_raw_info = Cardinal.set_plugin_load_order(dependency, plugins_raw_info)

                load_order = max(load_order, plugins_raw_info[dependency]['load_order']+1)

            plugin_raw_info['load_order'] = load_order

        return plugins_raw_info


    @staticmethod
    def get_module(module_path: Path) -> tuple[ModuleSpec, ModuleType]:
        '''
        Загружает модуль по указанному пути.

        :param module_path: Путь к модулю.
        :type module_path: Path
        :raises ModuleImportError: Ошибка при загрузке модуля.
        :return: Модуль.
        :rtype: tuple[ModuleSpec, ModuleType]
        '''
        try:
            spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except: raise exceptions.ModuleImportError(module_path)


        return spec, module


    def get_plugins_load_order(self, plugins_raw_info: dict[str, dict]):
        '''
        Получает порядок загрузки плагинов из информации о плагинах.

        :param plugins_raw_info: Информация о плагинах.
        :type plugins_raw_info: dict
        '''
        log.debug(self.translate('c_ext_getting_plugins_load_order'))

        self.plugins_load_order = list(plugins_raw_info)

        self.plugins_load_order.sort(key=lambda u: plugins_raw_info[u]['load_order'])

        log.debug(self.translate('c_ext_getting_plugins_load_order_success', self.plugins_load_order))


    def load_plugin(self, plugin_uuid: str):
        '''
        Загружает модуль плагина.

        :param module: Модуль.
        :type module: ModuleType
        :param module_path: Путь к модулю.
        :type module_path: Path
        :raises PluginNotTrustedException: Плагин отсутствует в списке trusted_plugins.
        :raises PluginDependenciesNotLoaded: Не загружены все зависимости плагина.
        '''
        plugin = self.plugins[plugin_uuid]


        log.debug(self.translate('c_ext_loading_plugin', plugin.name, plugin.uuid))

        if all([
            not self.config.plugins.load_all_plugins,
            not plugin_uuid in self.config.plugins.trusted_plugins
        ]): raise exceptions.PluginNotTrustedException(plugin)


        if any([not self.plugins[dependency].module for dependency in plugin.dependencies]): raise exceptions.PluginDependenciesNotLoadedError(plugin, plugin.dependencies)


        plugin_path = plugin.dir / 'plugin.py'

        plugin.spec, plugin.module = self.get_module(plugin_path)


        if hasattr(plugin.module, 'LOAD_PLUGIN'):
            log.debug(self.translate('c_ext_running_load_plugin_handlers', plugin.name, plugin.uuid))

            load_plugin_handlers = [Handler(plugin.uuid, 'LOAD_PLUGIN', 0, func) for func in getattr(plugin.module, 'LOAD_PLUGIN')]

            self.run_handlers(load_plugin_handlers)


        log.debug(self.translate('c_ext_plugin_load_success', plugin.name, plugin.uuid))

        return


    def init_plugins(self):
        'Инициализирует все загруженные плагины.'
        log.debug(self.translate('c_ext_initializing_plugins', len(self.plugins)))

        for plugin in self.plugins.values():
            try: self.init_plugin(plugin, self.event_var_names)
            except:
                log.error(self.translate('c_ext_initializing_plugin_err', plugin.name, plugin.uuid))
                log.debug('TRACEBACK', exc_info=True)

        log.info(self.translate('c_ext_initializing_plugins_success'))


    def init_plugin(self, plugin: Plugin, event_var_names: list[str]):
        '''
        Загружает хендлеры из плагина.

        :param plugin: Плагин.
        :type plugin: Plugin
        :param event_var_names: Список алиасов хендлеров.
        :type event_var_names: list[str]
        '''
        log.debug(self.translate('c_ext_initializing_plugin', plugin.name, plugin.uuid))


        if hasattr(plugin.module, 'INIT_PLUGIN'):
            log.debug(self.translate('c_ext_running_init_plugin_handlers', plugin.name, plugin.uuid))
            init_plugin_handlers = [
                Handler(
                    plugin.uuid,
                    'INIT_PLUGIN',
                    0,
                    func
                ) for func in getattr(plugin.module, 'INIT_PLUGIN')
            ]
            self.run_handlers(init_plugin_handlers)


        for event_name in event_var_names:
            if hasattr(plugin.module, event_name):
                log.debug(self.translate('c_ext_getting_plugin_handlers', event_name, getattr(plugin.module, event_name), plugin.uuid))

                for handler_value in getattr(plugin.module, event_name):
                    handler = Handler(
                        plugin.uuid,
                        event_name,
                        handler_value['priority'],
                        handler_value['handler']
                    )

                    plugin.handlers[event_name] = [*plugin.handlers.get(event_name, []), handler]


    def add_handlers_from_plugins(self):
        'Добавляет хендлеры из всех загруженных плагинов.'
        log.debug(self.translate('c_ext_adding_plugins_handlers', len(self.plugins)))

        for plugin in self.plugins.values(): self.add_handlers_from_plugin(plugin)


    def add_handlers_from_plugin(self, plugin: Plugin):
        '''
        Добавляет хендлеры из плагина в Кардинал.

        :param plugin: Плагин.
        :type plugin: Plugin
        '''
        log.debug(self.translate('c_ext_adding_plugin_handlers', plugin.name, plugin.uuid))

        for event_name, handlers in plugin.handlers.items():
            log.debug(self.translate('c_ext_adding_event_handlers', event_name, handlers, plugin.uuid))
            for handler in handlers: self.add_handler(handler, event_name)


    def add_handler(self, handler: Handler, event_var_name: str):
        '''
        Добавляет хендлер в Кардинал.

        :param handler: Хендлер.
        :type handler: Handler
        :param event_var_name: Алиас события хендлера.
        :type event_var_name: str
        '''
        log.debug(self.translate('c_ext_adding_handler', handler.func.__name__, handler.plugin_uuid, event_var_name))

        self.handlers[event_var_name] = [*self.handlers.get(event_var_name, []), handler]


    def run_handlers(self, handlers: list[Handler], *args, **kwargs):
        '''
        Запускает все хендлеры из списка с указанными аргументами

        :param handlers: Список хендлеров.
        :type handlers: list[Handler]
        '''
        if not handlers: return


        handlers.sort(key=lambda h: h.priority if h.priority >= 0 else inf)


        log.debug(self.translate('c_ext_running_handlers', handlers, args, kwargs))

        for handler in handlers: self.run_handler(handler, *args, **kwargs)


    def run_handler(self, handler: Handler, *args, **kwargs):
        '''
        Запускает хендлер с указанными аргументами.

        :param handler: Хендлер.
        :type handler: Handler
        '''
        log.debug(self.translate('c_ext_running_handler', getattr(handler.func, __name__, handler.plugin_uuid), args, kwargs))

        try: handler.func(self, *args, **kwargs)

        except:
            log.warning(self.translate('c_ext_running_handler_err', getattr(handler.func, __name__, handler.plugin_uuid)))
            log.debug(f'args={args} \nkwargs={kwargs}')
            log.debug('TRACEBACK', exc_info=True)

            self.run_handlers(self.handlers.get('HANDLER_ERROR', []), handler, args, kwargs)


    # ---------------------------------------------------------------------------- #
    #                               Методы FunPayAPI                               #
    # ---------------------------------------------------------------------------- #
    def get_balance(self, attempts: int = 3) -> Balance:
        '''
        Получает информацию о балансе.

        :param attempts: Кол-во попыток, defaults to 3.
        :type attempts: int, опционально
        :raises GetBalanceError: Не удалось получить баланс.
        :return: Баланс.
        :rtype: Balance
        '''
        def choice_random_lot() -> LotShortcut | None:
            '''
            Возвращает случайный лот из случайной категории для проверки баланса

            :return: Виджет лота.
            :rtype: LotShortcut | None
            '''
            for _ in range(3):
                subcat_id = random.choice(list(subcategories.keys()))

                lots = self.account.get_subcategory_public_lots(SubCategoryTypes.COMMON, subcat_id)


                if lots: break

            else: return

            return random.choice(lots)


        log.info(self.translate('c_ext_getting_balance'))

        for _ in range(attempts):
            try:
                subcategories = self.account.get_sorted_subcategories()[SubCategoryTypes.COMMON]


                lot = choice_random_lot()

                if not lot: continue


                balance = self.account.get_balance(lot.id)


                break


            except:
                log.warning(self.translate('c_ext_get_balance_unexcepted_err'))

                log.debug('TRACEBACK', exc_info=True)


                log.info(self.translate('c_ext_try_again_in_n_secs', 2))


                sleep(2)

                continue


        else:
            log.error(self.translate('c_ext_get_balance_too_many_attempts_err', attempts))

            log.debug('TRACEBACK', exc_info=True)


            raise exceptions.GetBalanceError()


        self.run_handlers(self.handlers.get('GET_BALANCE_SUCCESS', []), [balance])


        return balance


    def send_message(
            self, chat_id: int | str, message_text: str, chat_name: str | None = None,
            interlocutor_id: int | None = None, attempts: int = 3,
            watermark: bool = True
    ) -> list[Message] | None:
        '''
        Отправляет сообщение в чат FunPay.

        :param chat_id: ID чата.
        :param message_text: текст сообщения.
        :param chat_name: название чата (необязательно).
        :param interlocutor_id: ID собеседника (необязательно).
        :param attempts: кол-во попыток на отправку сообщения.
        :param watermark: добавлять ли водяной знак в начало сообщения?

        :return: объект сообщения / последнего сообщения, если оно доставлено, иначе - None
        '''
        if self.config.Other.watermark and watermark and not message_text.strip().startswith('$photo='):
            message_text = f'{self.config.Other.watermark}\n' + message_text


        entities = self.parse_message_entities(message_text)

        if all(isinstance(i, float) for i in entities) or not entities: return


        result = []

        for entity in entities:
            current_attempts = attempts

            while current_attempts:
                try:
                    if isinstance(entity, str):
                        msg = self.account.send_message(
                            chat_id,
                            entity,
                            chat_name,
                            interlocutor_id,
                            None,
                            not self.config.FunPay.oldMsgGetMode,
                            self.config.FunPay.oldMsgGetMode,
                            self.config.FunPay.keepSentMessagesUnread
                        )

                        result.append(msg)

                        log.info(self.translate('c_ext_msg_sent', chat_id))

                    elif isinstance(entity, int):
                        msg = self.account.send_image(
                            chat_id,
                            entity,
                            chat_name,
                            interlocutor_id,
                            not self.config.FunPay.oldMsgGetMode,
                            self.config.FunPay.oldMsgGetMode,
                            self.config.FunPay.keepSentMessagesUnread
                        )

                        result.append(msg)

                        log.info(self.translate('c_ext_msg_sent', chat_id))

                    elif isinstance(entity, float): sleep(entity)

                    break

                except Exception as ex:
                    log.warning(self.translate('c_ext_msg_send_err', chat_id))
                    log.debug('TRACEBACK', exc_info=True)

                    log.info(self.translate('c_ext_msg_attempts_left', current_attempts))

                    current_attempts -= 1
                    sleep(1)


            else:
                log.error(self.translate('c_ext_msg_no_more_attempts_err', chat_id))
                return []


        return result


    def get_exchange_rate(self, base_currency: Currencies, target_currency: Currencies, min_interval: int = 60): # TODO
        '''
        Получает курс обмена между двумя указанными валютами.
        Если с последней проверки прошло меньше `min_interval` секунд, используется сохранённое значение.

        :param base_currency: Исходная валюта, из которой производится обмен.
        :type base_currency: Currencies

        :param target_currency: Целевая валюта, в которую производится обмен.
        :type target_currency: Currencies

        :param min_interval: Минимальное время в секундах между проверками курса обмена.
        :type min_interval: :obj:`int`

        :return: Коэффициент обмена, где 1 единица `base_currency` = X единиц `target_currency`.
        :rtype: :obj:`float`
        '''
        assert base_currency != Currencies.UNKNOWN and target_currency != Currencies.UNKNOWN
        if base_currency == target_currency:
            return 1
        rate, t = self.__exchange_rates.get((base_currency, target_currency), (None, 0))
        if t and time() < t + min_interval:
            return rate
        for i in range(2, -1, -1):
            try:
                exchange_rate1, currency1 = self.account.get_exchange_rate(base_currency)
                self.__exchange_rates[(currency1, base_currency)] = (exchange_rate1, time())
                self.__exchange_rates[(base_currency, currency1)] = (1 / exchange_rate1, time())

                sleep(1)

                exchange_rate2, currency2 = self.account.get_exchange_rate(target_currency)
                self.__exchange_rates[(currency2, target_currency)] = (exchange_rate2, time())
                self.__exchange_rates[(target_currency, currency2)] = (1 / exchange_rate2, time())

                assert currency1 == currency2

                result = exchange_rate2 / exchange_rate1
                self.__exchange_rates[(base_currency, target_currency)] = (result, time())
                self.__exchange_rates[(target_currency, base_currency)] = (1 / result, time())

                return result
            except:
                log.warning(self.translate('c_ext_getting_exchange_rate_err', i))
                log.debug('TRACEBACK', exc_info=True)
                sleep(1)

        raise Exception('Не удалось получить курс обмена: превышено количество попыток.')


    # ---------------------------------------------------------------------------- #
    #                                   Настройки                                  #
    # ---------------------------------------------------------------------------- #
    @property
    def config(self): return Config(self.name)


    # ---------------------------------------------------------------------------- #
    #                                    Прочее                                    #
    # ---------------------------------------------------------------------------- #
    def translate(self, variable_name: str, *args, **kwargs):
        'Возвращает форматированный локализированный текст.'
        return Localizer().translate(self.config.language, variable_name, *args, **kwargs)


    def __create_greeting_text(self) -> str:
        'Генерирует приветствие для вывода в консоль после загрузки данных о пользователе.'
        current_time = datetime.now()

        if current_time.hour < 4:
            greetings = self.translate('c_ext_greetings_night_part')
        elif current_time.hour < 12:
            greetings = self.translate('c_ext_greetings_morning_part')
        elif current_time.hour < 17:
            greetings = self.translate('c_ext_greetings_day_part')
        else:
            greetings = self.translate('c_ext_greetings_evening_part')


        lines = [
            self.translate('c_ext_greetings_part_1', greetings, self.account.username),
            self.translate('c_ext_greetings_part_2', self.account.id),
            self.translate('c_ext_greetings_part_3', self.balance.total_rub, self.balance.total_usd, self.balance.total_eur),
            self.translate('c_ext_greetings_part_4', self.account.active_sales),
            self.translate('c_ext_greetings_part_5'),
        ]


        length = 60

        greetings_text = f'\n{'-' * length}\n'

        for line in lines:
            greetings_text += (
                line +
                ' ' * (
                    length - len(line.replace('$CYAN', '').replace('$YELLOW', '').replace('$MAGENTA', '').replace('$RESET', '')) - 1
                ) +
                '$RESET*\n'
            )

        greetings_text += f'{'-' * length}\n'


        return greetings_text


    @staticmethod
    def parse_message_entities(msg_text: str) -> list[str | int | float]:
        '''
        Разбивает сообщения по 20 строк, отделяет изображения от текста.
        (обозначение изображения: $photo=1234567890)

        :param msg_text: текст сообщения.

        :return: набор текстов сообщений / изображений.
        '''
        def split_text(text: str) -> list[str]:
            '''
            Разбивает текст на суб-тексты по 20 строк.

            :param text: исходный текст.

            :return: список из суб-текстов.
            '''
            output = []
            lines = text.split('\n')

            while lines:
                subtext = '\n'.join(lines[:20])
                del lines[:20]

                if (strip := subtext.strip()) and strip != '[a][/a]': output.append(subtext)


            return output


        msg_text = '\n'.join(i.strip() for i in msg_text.split('\n'))
        while '\n\n' in msg_text: msg_text = msg_text.replace('\n\n', '\n[a][/a]\n')


        pos = 0
        entities = []

        while entity := ENTITY_RE.search(msg_text, pos=pos):
            if text := msg_text[pos:entity.span()[0]].strip(): entities.extend(split_text(text))

            variable = msg_text[entity.span()[0]:entity.span()[1]]

            if variable.startswith('$photo'): entities.append(int(variable.split('=')[1]))
    
            elif variable.startswith('$sleep'): entities.append(float(variable.split('=')[1]))

            pos = entity.span()[1]

        else:
            if text := msg_text[pos:].strip(): entities.extend(split_text(text))

        return entities


__all__ = [
    'get_cardinal',
    'Cardinal'
]