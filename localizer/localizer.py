'Здесь описан класс локализатора.'
import logging


from . import LOCALES_DIR, ARG_PATTERN, KWARG_PATTERN
from .exceptions import *


from typing import Literal, Self
import json
from pathlib import Path


log = logging.getLogger('Localizer')


class Localizer:
    instance: Self = None


    def __new__(cls):
        if not cls.instance: cls.instance = super().__new__(cls)

        return cls.instance


    def __init__(self):
        if hasattr(self, '__initiated'): return

        self.__initiated = True
        'Флаг инициализации. Всегда True.'


        self.__load_locales()


    def __load_locales(self) -> None:
        'Выгружает переводы из locales.'
        log.debug('Получаю языки.')

        locales = 0

        for locale_path in LOCALES_DIR.glob('*.json'):
            locale_name = locale_path.stem


            try: locale = self.__get_locale(locale_name)
            except:
                log.warning(f'Не удалось загрузить язык {locale_name}.')
                log.debug('TRACEBACK', exc_info=True)

                continue


            setattr(self, locale_name, locale)
            locales+=1


        log.debug(f'Получено языков: {locales}.')

        return


    def __get_locale(self, locale: Literal['ru', 'en'] | str) -> dict[str, str]:
        'Возвращает файл перевода.'
        locale_path = LOCALES_DIR / f'{locale}.json'

        if not locale_path.exists(): raise LocaleNotFoundError(locale_path, locale_path.stem)


        try:
            with open(locale_path, encoding='utf-8') as fp: result = json.load(fp)

        except Exception as err: raise LocaleLoadError(locale_path, err)


        return result


    def translate(self, locale: Literal['ru', 'en'] | str, variable_name: str, *args, **kwargs) -> str:
        '''
        Возвращает форматированный локализированный текст.

        :param locale: Язык перевода.
        :type locale: str
        :param variable_name: Название переменной с текстом.
        :type variable_name: str
        :return: Форматированный локализированный текст.
        :rtype: str
        '''
        if not hasattr(self, locale):
            try: _ = self.__get_locale(locale)

            except LocaleNotFoundError:
                log.warning(f'Язык {locale} не найден (variable_name={variable_name}).')

                return variable_name

            except:
                log.warning(f'Непредвиденная ошибка при переводе (variable_name={variable_name}; locale={locale})')
                log.debug('TRACEBACK', exc_info=True)

                return variable_name


            setattr(self, locale, _)


        text: str | None = getattr(self, locale).get(variable_name)

        if not text:
            log.warning(f'Перевод {variable_name} не найден в локализации {locale}.')

            return variable_name


        try: return self.format_text(text, *args, **kwargs)
        except:
            log.warning(f'Не удалось отформатировать текст "{text}" (args={args}; kwargs={kwargs}).')
            log.debug('TRACEBACK', exc_info=True)


        return text


    def translate_from_file(self, from_file: Path, variable_name: str, *args, **kwargs) -> str:
        '''
        Выгружает перевод из файла. Возвращает форматированный локализированный текст.

        :param from_file: _description_
        :type from_file: str | Path
        :param variable_name: Название переменной с текстом.
        :type variable_name: str
        :return: Форматированный локализированный текст.
        :rtype: str
        '''
        with from_file.open('r', encoding='utf-8') as fp: localization_file = json.load(fp)


        text: str | None = localization_file.get(variable_name)

        if not text:
            log.warning(f'Перевод {variable_name} не найден в файле {from_file.stem}.')

            return variable_name


        try: return self.format_text(text, *args, **kwargs)
        except:
            log.warning(f'Не удалось отформатировать текст "{text}" (args={args}; kwargs={kwargs}).')
            log.debug('TRACEBACK', exc_info=True)


        return text


    def format_text(self, text: str, *args, **kwargs) -> str:
        _args = list(args)
        args_count = len(ARG_PATTERN.findall(text))
        kwords = KWARG_PATTERN.findall(text)

        if args_count < len(_args): _args.extend(['{}'] * (args_count - len(_args)))
        if text.count('{}') < len(_args): _args.extend(['{}'] * (text.count('{}') - len(_args)))

        for kword in kwords: kwargs[kword] = kwargs.get(kword, f'{{{kword}}}')

        try: return text.format(*_args, **kwargs)
        except Exception as err: raise FormatError(text, err, args, kwargs)


    def add_translation(self, locale: Literal['ru', 'en'] | str, variable_name: str, value: str, force_add: bool = False) -> None:
        '''
        Добавляет перевод в локализатор и соответствующий файл перевода.

        :param locale: Язык.
        :type locale: Literal[&#39;ru&#39;, &#39;en&#39;] | str
        :param variable_name: Имя переменной.
        :type variable_name: str
        :param value: Перевод.
        :type value: str
        :param force_add: Заменять перевод, если он уже существует, defaults to False
        :type force_add: bool, опционально
        '''
        if not hasattr(self, locale):
            try: _ = self.__get_locale(locale)

            except LocaleNotFoundError:
                with open(LOCALES_DIR / f'{locale}.json', 'w', encoding='utf-8') as fp: ...

                _ = self.__get_locale(locale)


            setattr(self, locale, _)


        current_localization = getattr(self, locale)

        if hasattr(current_localization, variable_name) and not force_add:
            log.debug(f'Не удалось добавить перевод {variable_name}, т.к. он уже есть в локализации {locale}.')

            return


        current_localization[variable_name] = value


        with open(LOCALES_DIR / f'{locale}.json', 'w', encoding='utf-8') as fp: json.dump(current_localization, fp)

        return


__all__ = [
    'Localizer'
]