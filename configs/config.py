'Здесь описан основной класс конфига бота.'
from . import CONFIGS_DIR

from dynaconf import Dynaconf
from dynaconf import loaders as DynaLoaders


import tomllib


from pathlib import Path
from threading import Lock
from typing import Any


class Config:
    __locks: dict[str, Lock] = {
        'init_lock': Lock(),
        'default_lock': Lock()
    }


    __settings_files: dict[str, Path] = {}
    'Список загружаемых файлов конфигов с соответствующими именами секций.'


    def __init__(self, section: str | None = None):
        '''
        Класс конфига.

        :param section: Секция конфига, отображаемая в Config.config, defaults to None.
        :type section: str | None, опционально
        '''
        with Config.__locks['init_lock']:
            self.__section = section
            'Секция конфига, отображаемая в Config.config.'


            self.update_config()


            self.__lock = self.__get_lock()
            'Lock для указанной секции конфига.'


    def __getattribute__(self, name):
        try: return super().__getattribute__(name)
        except: return self.config[name]


    @classmethod
    def init_config(cls) -> None:
        '''
        Проходит по всем конфигам в папке конфигов, считывает секции и добавляет в загружаемые конфиги.
        '''
        for config_path in CONFIGS_DIR.glob('*.toml'):
            if config_path in cls.__settings_files.values(): continue


            with config_path.open('rb') as fp: config = tomllib.load(fp)
            sections = [*config]

            cls.add_config_file(config_path, sections)


        return


    @classmethod
    def add_config_file(cls, config_path: Path, section_names: list[str] | None = None) -> None:
        '''
        Добавляет путь к файлу конфига в список конфигов для загрузки.

        Указывайте все имена секций в конфиге.
        При отсутствии параметра section_names будет установлено единственное имя секции, соответствующее имени конфига (большими буквами).

        Файл конфига без секций или с несоответствующими указанным в section_names секциям при обновлении конфига ПОЛНОСТЬЮ ОЧИСТИТСЯ!

        ВАЖНО!!! Не обновляет сам конфиг. Для обновления используйте config.update_config() или инициализируйте класс повторно.

        :param config_path: Путь к конфигу.
        :type config_path: Path
        :param section_names: Имена секций в конфиге, defaults to None.
        :type section_names: list[str] | None, опционально
        :raises ValueError: Если имя секции уже есть в списке конфигов.
        '''
        if not section_names: section_names = [config_path.stem.upper()]

        for section_name in section_names:
            if Config.__settings_files.get(section_name, None): raise ValueError(f'Конфиг с указанным именем секции {section_name} уже существует!')

            Config.__settings_files[section_name] = config_path


        return


    def __get_config(self) -> Dynaconf:
        settings_files = self.__settings_files_list

        return Dynaconf(
            settings_files=settings_files,
            environments=True if self.__section else False,
            env=self.__section
        )


    def update_config(self) -> None:
        '''
        Повторно инициализирует Config.config.

        ВАЖНО!!! Не сохраняет изменения. Для сохранения изменений используйте Config.save()
        '''
        self.config = self.__get_config()


        return


    def save(self, force_save: bool = False) -> None:
        '''
        Сохраняет изменения в файле (файлах) конфига.

        :param force_save: Игнорировать Lock, defaults to False.
        :type force_save: bool, опционально
        '''
        def save_without_section():
            config_paths_sections: dict[Path, list[str]] = {}

            for section_name in Config.__settings_files:
                config_path = Config.__settings_files[section_name]

                config_paths_sections[config_path] = list(set(config_paths_sections.get(config_path, []) + [section_name]))


            for config_path in config_paths_sections:
                config_sections = config_paths_sections[config_path]


                config_dict: dict[str, dict] = {}

                for section_name in config_sections: config_dict[section_name] = self.config.to_dict()[section_name]


                DynaLoaders.write(str(config_path), config_dict)


        def save_with_section():
            config_file_path: Path = Config.__settings_files[self.__section]

            sections_to_save: list[str] = self.__get_same_config_file_sections()


            settings_files = self.__settings_files_list

            configs: dict[str, Dynaconf] = {
                section_name: Dynaconf(
                settings_files=settings_files,
                environments=True,
                env=section_name
            ) for section_name in sections_to_save
            }


            end_config_dict: dict[str, Any] = {self.__section: self.config.to_dict()}

            end_config_dict.update(
                {section_name: config.to_dict() for section_name, config in configs.items()}
            )


            DynaLoaders.write(str(config_file_path), end_config_dict)


            return


        if not force_save: self.__lock.acquire()


        if self.__section: save_with_section()


        else: save_without_section()


        if not force_save: self.__lock.release()


        self.update_config()

        return


    def __get_same_config_file_sections(self) -> list[str] | None:
        '''
        Возвращает список всех секций (кроме текущей), используемых в том же файле, что и секция текущего конфига.

        :return: None, если не была указана секция, иначе список секций.
        :rtype: list[str] | None
        '''
        if not self.__section: return None


        config_file_path: Path = Config.__settings_files[self.__section]


        sections: list[str] = []

        for section_name in Config.__settings_files:
            if self.__section != section_name and Config.__settings_files[section_name] == config_file_path: sections.append(config_file_path)


        return sections


    @property
    def __settings_files_list(self) -> list[Path]:
        '''
        Список уникальных путей в Config.__settings_files.
        '''
        return list(set(list(Config.__settings_files.values())))


    def __get_lock(self):
        '''
        Возвращает Lock для указанной секции конфига.
        '''
        if not self.__section: return Config.__locks['default_lock']


        if Config.__locks.get(self.__section): return Config.__locks.get(self.__section)


        sections =  self.__get_same_config_file_sections()

        if not sections:
            Config.__locks[self.__section] = Lock()

            return Config.__locks.get(self.__section)


        for section in sections:
            if Config.__locks.get(section):
                Config.__locks[self.__section] = Config.__locks.get(section)

                return Config.__locks.get(self.__section)


        
        Config.__locks[self.__section] = Lock()

        return Config.__locks.get(self.__section)


__all__ = [
    'Config'
]