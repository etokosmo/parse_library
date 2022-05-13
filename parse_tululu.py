import argparse
import os
from pathlib import Path
from typing import Tuple
from urllib.parse import urljoin, urlsplit, unquote_plus

import requests
from bs4 import BeautifulSoup
from pathvalidate import is_valid_filename, sanitize_filename
from retry import retry


def check_for_redirect(response: requests.models.Response) -> None:
    """Проверяем ссылку на редирект"""
    if response.history:
        raise requests.HTTPError


@retry(requests.exceptions.ConnectionError, tries=3, delay=10)
def download_txt(url: str, params: dict, filename: str, folder: str = 'books/') -> str:
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    if not is_valid_filename(filename):
        filename = sanitize_filename(filename)
    path_to_download = os.path.join(folder, filename)
    Path(folder).mkdir(parents=True, exist_ok=True)

    response = requests.get(url, params=params)
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
    path_to_download = os.path.join(folder, str(filename))
    Path(folder).mkdir(parents=True, exist_ok=True)

    response = requests.get(url)
    check_for_redirect(response)
    response.raise_for_status()

    full_path_to_download = f"{path_to_download}{file_extension}"
    with open(full_path_to_download, 'wb') as file:
        file.write(response.content)

    return full_path_to_download


def parse_book_page(content) -> dict:
    """Возвращаем словарь с данными о книге: название, автор, ссылка на фото, список комментариев, список жанров"""
    title_tag = content.find('h1')
    book_title, book_author = [text.strip() for text in title_tag.text.strip().split("::")]

    all_comments = [comment.find('span').text for comment in content.find_all('div', class_='texts')]
    all_genres = [genre.text for genre in content.find('span', class_='d_book').find_all('a')]

    book_image = content.find('div', class_='bookimage').find('img')['src']
    book_image = urljoin('https://tululu.org/', book_image)

    book_info = {
        'title': book_title,
        'author': book_author,
        'image': book_image,
        'genres': all_genres,
        'comments': all_comments
    }
    return book_info


@retry(requests.exceptions.ConnectionError, tries=3, delay=10)
def get_book_info(book_id: int) -> dict:
    """Парсим страницу книги и вовзращаем словарь с данными о книге"""
    url = f'https://tululu.org/b{book_id}/'

    response = requests.get(url)
    check_for_redirect(response)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    return parse_book_page(soup)


def main():
    parser = argparse.ArgumentParser(
        description='Скрипт для скачивания книг'
    )
    parser.add_argument('--start_id', help='С какой страницы начать скачивание', type=int, default=1)
    parser.add_argument('--end_id', help='На какой странице закончить скачивание', type=int, default=2)
    args = parser.parse_args()
    start = args.start_id
    if start < 1:
        start = 1
    end = args.end_id
    if end <= start:
        end = start + 1

    for book_id in range(start, end + 1):
        book_url = f"https://tululu.org/txt.php"
        payload = {"id": book_id}
        try:
            book_info = get_book_info(book_id)
            download_txt(book_url, payload, f"{book_id}. {book_info.get('title')}")
            download_image(book_info.get('image'))
            print("Название:", book_info.get('title'))
            print("Автор:", book_info.get('author'))
        except requests.exceptions.HTTPError:
            continue
        except requests.exceptions.ConnectionError:
            print("Потеряно соединение...")


if __name__ == "__main__":
    main()
