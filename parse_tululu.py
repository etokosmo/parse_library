import argparse
import os
import re
from pathlib import Path
from typing import Tuple
from urllib.parse import urljoin, urlsplit, unquote_plus

import requests
from bs4 import BeautifulSoup
from loguru import logger
from pathvalidate import is_valid_filename, sanitize_filename
from retry import retry

BASE_DIR = os.path.dirname(__file__) or '.'
PATH_TO_LOGS = os.path.join(BASE_DIR, 'logs', 'logs.log')


def check_for_redirect(response: requests.models.Response) -> None:
    """Проверяем ссылку на редирект"""
    if response.history:
        raise requests.HTTPError


@retry(requests.exceptions.ConnectionError, tries=3, delay=10)
def download_txt(url: str, filename: str, folder: str = 'books/') -> str:
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    pattern_to_find_id = r'\d+'
    book_id = re.search(pattern_to_find_id, url).group()
    book_url_download = f"https://tululu.org/txt.php"
    payload = {"id": book_id}

    if not is_valid_filename(filename):
        filename = sanitize_filename(filename)
    path_to_download = os.path.join(folder, filename)
    Path(folder).mkdir(parents=True, exist_ok=True)

    response = requests.get(book_url_download, params=payload)
    check_for_redirect(response)
    response.raise_for_status()

    full_path_to_download = f"{path_to_download}.txt"
    with open(full_path_to_download, 'wb') as file:
        file.write(response.content)

    return full_path_to_download


def get_filename_and_file_extension(url: str) -> Tuple[str, str]:
    """Получаем название файла и расширение файла из ссылки"""
    truncated_url = unquote_plus(urlsplit(url, scheme='', allow_fragments=True).path)
    filename, file_extension = os.path.splitext(truncated_url)
    filename = filename.split("/")[-1]
    return filename, file_extension


@retry(requests.exceptions.ConnectionError, tries=3, delay=10)
def download_image(url: str, folder: str = 'images/') -> str:
    """Функция для скачивания изображений"""
    filename, file_extension = get_filename_and_file_extension(url)
    path_to_download = os.path.join(folder, filename)
    Path(folder).mkdir(parents=True, exist_ok=True)

    response = requests.get(url)
    check_for_redirect(response)
    response.raise_for_status()

    full_path_to_download = f"{path_to_download}{file_extension}"
    with open(full_path_to_download, 'wb') as file:
        file.write(response.content)

    return full_path_to_download


def parse_book_page(content, url: str) -> dict:
    """Возвращаем словарь с данными о книгах:
    название, автор, ссылка на фото, список комментариев, список жанров, ссылка на книгу"""
    title_tag = content.select_one('h1')
    book_title, book_author = [text.strip() for text in title_tag.text.strip().split("::")]

    all_comments = [comment.select_one('span').text for comment in content.select('div.texts')]
    all_genres = [genre.text for genre in content.select('span.d_book a')]

    book_image = content.select_one('div.bookimage img')['src']
    book_image = urljoin(url, f"{book_image}")

    book_info = {
        'title': book_title,
        'author': book_author,
        'image': book_image,
        'genres': all_genres,
        'comments': all_comments,
        'book_url': url
    }
    return book_info


@retry(requests.exceptions.ConnectionError, tries=3, delay=10)
def get_book(book_id: int = 1, url: str | None = None) -> dict:
    """Парсим страницу книги и возвращаем словарь с данными о книге"""
    if not url:
        url = f'https://tululu.org/b{book_id}/'

    response = requests.get(url)
    check_for_redirect(response)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    return parse_book_page(soup, url)


def main():
    logger.add(PATH_TO_LOGS, level='DEBUG')

    parser = argparse.ArgumentParser(
        description='Скрипт для скачивания книг'
    )
    parser.add_argument('--start_id', help='С какого id книги начать скачивание', type=int, default=1)
    parser.add_argument('--end_id', help='На каком id книги закончить скачивание', type=int, default=2)
    args = parser.parse_args()
    logger.info(f'Прием аргументов: start_id={args.start_id}, end_id={args.end_id}')

    start = args.start_id
    if start < 1:
        start = 1
    end = args.end_id
    if end <= start:
        end = start + 1
    logger.info(f'Аргументы после обработки: start_id={start}, end_id={end}')

    for book_id in range(start, end):
        try:
            book = get_book(book_id)
            logger.info(f'book_id={book_id}. Получили book_info')
            download_txt(book.get('book_url'), f"{book_id}. {book.get('title')}")
            logger.info(f'book_id={book_id}. Скачали книгу')
            download_image(book.get('image'))
            logger.info(f'book_id={book_id}. Скачали изображение')
        except requests.exceptions.HTTPError:
            logger.debug(f'HTTP Error. Страницы с id={book_id} не существует.')
        except requests.exceptions.ConnectionError:
            logger.debug(f'Потеряно соединение...Текущая сессия: id={book_id}.')


if __name__ == "__main__":
    main()
