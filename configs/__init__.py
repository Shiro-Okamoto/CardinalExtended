
from pathlib import Path


# ---------------------------------------------------------------------------- #
#                               Пути и директории                              #
# ---------------------------------------------------------------------------- #
HOME_DIR = Path(__file__).parent.parent
'Путь к папке Кардинала.'


CONFIGS_DIR = HOME_DIR / 'configs'
'Путь к папке с конфигами.'

LOGGER_CONFIG_PATH = CONFIGS_DIR / 'logger_config.toml'
'Путь к конфигу логгера.'

DEFAULT_CARDINAL_CONFIG_PATH = CONFIGS_DIR / 'default_cardinal_config.toml'
'Путь к папке со стандартными настройками Кардинала.'


VERSION_PATH = HOME_DIR / 'VERSION.md'
'Путь к версии Кардинала.'


LOGS_DIR = HOME_DIR / 'logs'
'Путь к папке с логами.'


STORAGE_DIR = HOME_DIR / 'storage'
'Путь к папке с кешем и т.д.'

CACHE_DIR = STORAGE_DIR / 'cache'
'Путь к папке с кешем.'

UPDATE_DIR = CACHE_DIR / 'update'
'Путь к папке со скачанным обновлением.'

BACKUP_DIR = CACHE_DIR / 'backup'
'Путь к папке с бекапами.'


PLUGINS_DIR = HOME_DIR / 'plugins'
'Путь к папке с плагинами.'


from .config import *


__all__ = [
    'HOME_DIR',

    'CONFIGS_DIR',
    'LOGGER_CONFIG_PATH',
    'DEFAULT_CARDINAL_CONFIG_PATH',

    'VERSION_PATH',

    'LOGS_DIR',

    'STORAGE_DIR',
    'CACHE_DIR',
    'UPDATE_DIR',
    'BACKUP_DIR',

    'PLUGINS_DIR',

    'Config'
]