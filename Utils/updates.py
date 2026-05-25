
import shutil


from . import Tag, Release, exceptions
from configs import CONFIGS_DIR, STORAGE_DIR, PLUGINS_DIR, CACHE_DIR, UPDATE_DIR, BACKUP_DIR


import requests
from zipfile import ZipFile


from pathlib import Path
from time import sleep


HEADERS = {
    "accept": "application/vnd.github+json"
}


# ---------------------------------------------------------------------------- #
#                                  Обновления                                  #
# ---------------------------------------------------------------------------- #

# ----------------------------------- Теги ----------------------------------- #
def get_tags(tag: str, github_api_url: str) -> list[Tag]:
    '''
    Получает все теги с GitHub репозитория.

    :param tag: Текущий тег.
    :type tag: str
    :param github_api_url: Ссылка на апи репозитория (api.github.com/repos/{user}/{repo}).
    :type github_api_url: str
    :raises GitHubRequestError: Если не удалось получить список тегов.
    :return: Список тегов.
    :rtype: list[dict[str, Any]]
    '''
    page = 1
    result: list[Tag] = []

    while True:
        if page != 1: sleep(1)


        response = requests.get(f"{github_api_url}/tags?page={page}", headers=HEADERS)


        json_response = response.json()

        if response.status_code != 200 or not json_response: break


        tags = [Tag(json=_) for _ in json_response]

        result.extend(tags)


        if tag is not None and any([_tag.name == tag for _tag in tags]): break


        page+=1


    if not result: raise exceptions.GitHubRequestError(response)


    return result


def get_next_tag(tags: list[Tag], tag: str) -> Tag | None:
    '''
    Ищет след. тег после переданного. Если не находит текущий тег, возвращает первый. Если текущий тег - последний, возвращает None.

    :param tags: Список тегов.
    :type tags: list[Tag]
    :param tag: Текущий тег.
    :type tag: str
    :raises GetNextTagError: Если не удалось найти тег в списке.
    :return: След. тег / первый тег / None.
    :rtype: str | None
    '''
    for current_index in range(len(tags)):
        if tags[current_index].name == tag: break

    else: raise exceptions.GetNextTagError(tag, tags)


    if not current_index: return None


    return tags[current_index - 1]


# ---------------------------------- Релизы ---------------------------------- #
def get_releases(github_api_url: str, from_tag: Tag | None = None) -> list[Release]:
    '''
    Получает данные о доступных релизах, начиная с тега.

    :param from_tag: Тег релиза, с которого начинать поиск, defaults to None.
    :type from_tag: Tag | None, опционально
    :param github_api_url: Ссылка на апи репозитория (api.github.com/repos/{user}/{repo}).
    :type github_api_url: str
    :raises ReleaseNotFoundError: Если не удалось найти релиз с тегом from_tag.
    :return: Список релизов.
    :rtype: list[Release]
    '''
    page = 1
    result: list[Release] = []
    while True:
        if page != 1: sleep(1)


        response = requests.get(f"{github_api_url}/releases?page={page}", headers=HEADERS)


        json_response = response.json()

        if response.status_code != 200 or not json_response: break


        releases = [Release(json=release) for release in json_response]

        result.extend(releases)


        if from_tag is not None and any([release.tag_name == from_tag.name for release in releases]): break


        page+=1


    if not result: raise exceptions.GitHubRequestError(response)


    result.reverse()


    if from_tag:
        from_index = None
        for from_index in range(len(result)):
            if result[from_index].tag_name == from_tag.name: break

        else: raise exceptions.ReleaseNotFoundError(from_tag, result)


        result = result[from_index:]


    return result


def get_new_releases(current_tag: str, github_api_url: str) -> list[Release] | None:
    '''
    Проверяет на наличие обновлений.

    :param tag: Текущий тег.
    :type tag: str
    :param github_api_url: Ссылка на апи репозитория (api.github.com/repos/{user}/{repo}).
    :type github_api_url: str
    :raises exceptions.GetNewReleasesError: Если не удалось получить список релизов.
    :return: Список релизов, если найдена новая версия.
    :rtype: list[Release] | None
    '''
    tags = get_tags(current_tag, github_api_url)


    next_tag = get_next_tag(tags, current_tag)

    if not next_tag: return None


    releases = get_releases(github_api_url, next_tag)

    if not releases: raise exceptions.GetNewReleasesError(next_tag)


    return releases


# --------------------------------- Установка -------------------------------- #
def download_release(release: Release) -> None:
    '''
    Скачивает архив релиза.

    :param release: Релиз.
    :type release: Release
    '''
    download_zip(release.zipball_url, CACHE_DIR / 'update.zip')


    return


def extract_release() -> str:
    '''
    Разархивирует архив с обновлением.

    :return: Имя папки с обновлением.
    :rtype: str
    '''
    update_folder = extract_archive(CACHE_DIR / 'update.zip', UPDATE_DIR)


    return update_folder


def install_release(folder_name: str) -> None:
    '''
    Устанавливает обновление.

    :param folder_name: Название папки со скачанным обновлением в папке обновлений.
    :type folder_name: str
    '''

    release_folder = UPDATE_DIR.joinpath(folder_name)


    for _ in release_folder.iterdir():
        file = _.name

        if _.is_file(): shutil.copy2(_, file)
        else: shutil.copytree(_, file, dirs_exist_ok=True)


    return


# ---------------------------------------------------------------------------- #
#                                    Бекапы                                    #
# ---------------------------------------------------------------------------- #
def create_backup() -> None:
    '''
    Создает резервную копию с папками storage, configs и plugins.
    '''
    with ZipFile("backup.zip", "w") as zip:
        zipdir(CONFIGS_DIR, zip)
        zipdir(STORAGE_DIR, zip)
        zipdir(PLUGINS_DIR, zip)


    return


def extract_backup_archive() -> None:
    '''
    Разархивирует скачанный backup.zip в папку бекапа.
    '''
    extract_archive('backup.zip', BACKUP_DIR)


    return


def install_backup() -> None:
    '''
    Устанавливает бекап.

    :raises BackupNotFoundError: Если отсутствует распакованный бекап.
    '''
    if not BACKUP_DIR.exists(): raise exceptions.BackupNotFoundError()


    for _ in BACKUP_DIR.iterdir():
        file = _.name

        if _.is_file(): shutil.copy2(_, file)

        else: shutil.copytree(_, file, dirs_exist_ok=True)


    return


# ---------------------------------------------------------------------------- #
#                               Работа с файлами                               #
# ---------------------------------------------------------------------------- #
def download_zip(url: str, zip_path: Path) -> None:
    '''
    Загружает zip архив с обновлением.

    :param url: Ссылка на zip архив.
    :type url: str
    :param zip_path: Конечный путь.
    :type zip_path: Path
    '''
    with requests.get(url, stream=True) as r:
        r.raise_for_status()

        with open(zip_path, 'wb') as fp:
            for chunk in r.iter_content(chunk_size=8192): fp.write(chunk)


    return


def extract_archive(zip_path: Path, path: Path) -> str:
    '''
    Разархивирует архив.

    :param zip_path: Путь к архиву.
    :type zip_path: Path
    :param path: Конечный путь.
    :type path: Path
    :return: Название папки с обновлением (storage/cache/update/<папка с обновлением>).
    :rtype: str
    '''
    if path.exists(): shutil.rmtree(path, ignore_errors=True)

    path.mkdir(parents=True, exist_ok=True)


    with ZipFile(zip_path, "r") as zip:
        folder_name = zip.filelist[0].filename

        zip.extractall(path)


    return folder_name


def zipdir(path: Path, zip_obj: ZipFile) -> None:
    '''
    Рекурсивно архивирует папку.

    :param path: Путь до папки.
    :type path: Path
    :param zip_obj: Объект zip архива.
    :type zip_obj: ZipFile
    '''
    for root, dirs, files in path.walk():
        if root.name == "__pycache__": continue

        for file in files: zip_obj.write(root.joinpath(file), root.joinpath(file).relative_to(path.parent))


    return


__all__ = [
    'get_tags',
    'get_next_tag',
    'get_releases',
    'get_new_releases',
    'download_release',
    'extract_release',
    'install_release',
    'create_backup',
    'extract_backup_archive',
    'install_backup',
    'download_zip',
    'extract_archive',
    'zipdir'
]