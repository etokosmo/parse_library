import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from loguru import logger
from retry import retry

from parse_tululu import download_txt, download_image, get_book

BASE_DIR = os.path.dirname(__file__) or '.'
PATH_TO_LOGS = os.path.join(BASE_DIR, 'logs', 'logs.log')


def check_for_redirect(response: requests.models.Response) -> None:
    """Проверяем ссылку на редирект"""
    if response.history:
        raise requests.HTTPError


def make_json(content: list[dict], filename: str = 'books.json', folder: str = '') -> None:
    path_to_download = os.path.join(folder, filename)
    Path(folder).mkdir(parents=True, exist_ok=True)
    with open(path_to_download, "w", encoding='utf8') as file:
        json.dump(content, file, ensure_ascii=False)


@retry(requests.exceptions.ConnectionError, tries=3, delay=10)
def get_books_of_category(category: str, count_page: int = 1) -> list[dict]:
    """Возвращаем список словарей с данными о книгах:
    название, автор, ссылка на фото, список комментариев, список жанров, ссылка на книгу"""

    books = []
    for page in range(1, count_page + 1):
        url = f'https://tululu.org/{category}/{page}/'
        logger.info(f'url={url}')
        response = requests.get(url)
        check_for_redirect(response)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        for book_page in soup.find_all('table', class_='d_book'):
            book_number = book_page.find('a')['href']
            pattern_to_find_id = r'\d+'
            book_id = re.search(pattern_to_find_id, book_number).group()
            book_link = urljoin(url, book_number)
            logger.info(f'id={book_id}')

            try:
                book = get_book(url=book_link)
                logger.info(f'url={book_link}. Получили book_info')
                download_txt(book.get('book_url'), f"{book_id}. {book.get('title')}")
                logger.info(f'url={book_link}. Скачали книгу')
                download_image(book.get('image'))
                logger.info(f'url={book_link}. Скачали изображение')
                books.append(book)
            except requests.exceptions.HTTPError:
                logger.debug(f'HTTP Error. book_id={book_id} - Нельзя скачать кингу.')
            except requests.exceptions.ConnectionError:
                logger.debug(f'Потеряно соединение...Текущая сессия: book_id={book_id}.')
    make_json(books)
    return books


if __name__ == "__main__":
    book_category = "l55"
    count_pages = 1

    logger.add(PATH_TO_LOGS, level='DEBUG')
    try:
        get_books_of_category(book_category, count_pages)
        logger.info(f'category={book_category}. Получили книги со страниц по категории')
    except requests.exceptions.HTTPError:
        logger.debug(f'HTTP Error. category={book_category} - Нет страницы с такой категорией.')
    except requests.exceptions.ConnectionError:
        logger.debug(f'Потеряно соединение...Текущая сессия: category={book_category}.')
