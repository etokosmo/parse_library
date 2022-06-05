import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, element
from loguru import logger
from retry import retry

from parse_tululu import download_txt, download_image, get_book, \
    check_for_redirect

BASE_DIR = os.path.dirname(__file__) or '.'
PATH_TO_LOGS = os.path.join(BASE_DIR, 'logs', 'logs.log')
BOOK_CATEGORY = "l55"
PATTERN_TO_FIND_BOOK_ID = r'\d+'


@dataclass
class ParseArgs:
    start_page: int
    end_page: int
    skip_imgs: bool
    skip_txt: bool
    dest_folder: str
    json_path: str


def get_last_page(category: str) -> int:
    """Возвращаем последнюю страницу категории"""
    url = f'https://tululu.org/{category}/'
    response = requests.get(url)
    check_for_redirect(response)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    page_selector = "#content .center .npage"
    last_page = soup.select(page_selector)[-1].text
    return int(last_page)


def save_json(content: list[dict],
              filename: str = 'books.json',
              folder: str = '') -> None:
    """Сохраняем JSON файл"""
    path_to_download = os.path.join(folder, filename)
    Path(folder).mkdir(parents=True, exist_ok=True)
    with open(path_to_download, "w", encoding='utf8') as file:
        json.dump(content, file, ensure_ascii=False)


def get_book_pages(url) -> element.ResultSet:
    """Получаем все ссылки всех книг на странице"""
    logger.info(f'url={url}')
    response = requests.get(url)
    check_for_redirect(response)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    book_selector = "table.d_book div.bookimage a"
    return soup.select(book_selector)


@retry(requests.exceptions.ConnectionError, tries=3, delay=10)
def get_books_of_category(book_pages: list,
                          url_category_page: str,
                          book_id_pattern: str,
                          parseargs: ParseArgs) -> list[dict]:
    """Возвращаем список словарей с данными о книгах:
    название, автор, ссылка на фото, список комментариев, список жанров,
    ссылка на книгу"""
    books = []
    path_to_download_books = urljoin(parseargs.dest_folder, "books/")
    path_to_download_images = urljoin(parseargs.dest_folder, "images/")
    for book_page in book_pages:
        book_number = book_page['href']
        book_id = re.search(book_id_pattern, book_number).group()
        book_link = urljoin(url_category_page, book_number)
        logger.info(f'id={book_id}')

        try:
            book = get_book(url=book_link)
            logger.info(f'url={book_link}. Получили book_info')
            if not parseargs.skip_txt:
                path_to_txt = download_txt(
                    book.get('book_url'),
                    f"{book_id}. {book.get('title')}",
                    path_to_download_books
                )
                book['path_to_txt'] = path_to_txt
                logger.info(f'url={book_link}. Скачали книгу')
            if not parseargs.skip_imgs:
                path_to_img = download_image(
                    book.get('image'),
                    path_to_download_images
                )
                book['path_to_img'] = path_to_img
                logger.info(f'url={book_link}. Скачали изображение')
            books.append(book)
        except requests.exceptions.HTTPError:
            logger.debug(
                f'HTTP Error. book_id={book_id} - Нельзя скачать кингу.')
        except requests.exceptions.ConnectionError:
            logger.debug(
                f'Потеряно соединение...Текущая сессия: book_id={book_id}.')
    return books


def get_arguments(category: str):
    """Принимает аргументы из консоли"""
    parser = argparse.ArgumentParser(description='Скрипт для скачивания книг')
    parser.add_argument(
        '--start_page',
        help='С какой страницы начать скачивание', type=int,
        default=1
    )
    parser.add_argument(
        '--end_page',
        help='На какой странице закончить скачивание',
        type=int,
        default=get_last_page(category) + 1
    )
    parser.add_argument(
        '--dest_folder',
        help='Путь к каталогу с результатами парсинга: картинкам,книгам,JSON',
        default=''
    )
    parser.add_argument(
        '--skip_imgs',
        action='store_true',
        help='Не скачивать картинки'
    )
    parser.add_argument(
        '--skip_txt',
        action='store_true',
        help='Не скачивать книги'
    )
    parser.add_argument(
        '--json_path',
        help='Указать свой путь к *.json файлу с результатами',
        default=''
    )
    return parser.parse_args()


def process_args(arguments) -> ParseArgs:
    """Обрабатываем аргументы на возможные ошибки"""
    start = arguments.start_page
    if start < 1:
        start = 1
    end = arguments.end_page
    if end <= start:
        end = start + 1
    if arguments.dest_folder and not arguments.dest_folder.endswith('/'):
        arguments.dest_folder += '/'
    if arguments.json_path and not arguments.json_path.endswith('/'):
        arguments.json_path += '/'

    logger.info(
        f'Аргументы после обработки: start_id={start}, end_id={end}, \
        dest_folder={arguments.dest_folder}, json_path={arguments.json_path}')

    args = ParseArgs(
        start_page=arguments.start_page,
        end_page=arguments.end_page,
        skip_imgs=arguments.skip_imgs,
        skip_txt=arguments.skip_txt,
        dest_folder=arguments.dest_folder,
        json_path=arguments.json_path
    )
    return args


def main():
    logger.add(PATH_TO_LOGS, level='DEBUG')

    args = get_arguments(BOOK_CATEGORY)
    logger.info(
        f'Прием аргументов: start_id={args.start_page}, \
        end_id={args.end_page}, dest_folder={args.dest_folder}, \
        skip_imgs={args.skip_imgs}, skip_txt={args.skip_txt}, \
        json_path={args.json_path}')

    parse_args = process_args(args)
    books = []
    for page in range(parse_args.start_page, parse_args.end_page):
        url_category_page = f'https://tululu.org/{BOOK_CATEGORY}/{page}/'
        try:
            book_pages = get_book_pages(url_category_page)
            books.extend(get_books_of_category(
                book_pages,
                url_category_page,
                PATTERN_TO_FIND_BOOK_ID,
                parse_args))

            logger.info(f'category={BOOK_CATEGORY}. \
            Получили книги со страниц по категории')
        except requests.exceptions.HTTPError:
            logger.debug(
                f'HTTP Error. category={BOOK_CATEGORY} - \
                Нет страницы page={page} с такой категорией.')
        except requests.exceptions.ConnectionError:
            logger.debug(
                f'Потеряно соединение...Текущая сессия: \
                category={BOOK_CATEGORY}.')
    save_json(
        books,
        folder=parse_args.json_path if parse_args.json_path else parse_args.dest_folder
    )


if __name__ == "__main__":
    main()
