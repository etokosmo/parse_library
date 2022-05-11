import os
from pathlib import Path
from typing import Tuple
from urllib.parse import urljoin, urlsplit, unquote_plus

import requests
from bs4 import BeautifulSoup
from pathvalidate import is_valid_filename, sanitize_filename

PATH_TO_DOWNLOAD = "books"
Path(PATH_TO_DOWNLOAD).mkdir(parents=True, exist_ok=True)


def get_request(url) -> requests.models.Response:
    """Отправляем запрос"""
    response = requests.get(url)
    check_for_redirect(response)
    response.raise_for_status()
    return response


def check_for_redirect(response: requests.models.Response) -> None:
    """Проверяем ссылку на редирект"""
    if response.history:
        raise requests.HTTPError


def download_txt(url: str, filename: str, folder: str = 'books/') -> str:
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

    response = get_request(url)

    Path(folder).mkdir(parents=True, exist_ok=True)
    with open(f"{path_to_download}.txt", 'wb') as file:
        file.write(response.content)

    return f"{path_to_download}.txt"


def get_filename_and_file_extension(url: str) -> Tuple[str, str]:
    """Получаем название файла и расширение файла из ссылки"""
    truncated_url = unquote_plus(urlsplit(url, scheme='', allow_fragments=True).path)
    filename, file_extension = os.path.splitext(truncated_url)
    filename = filename.split("/")[-1]
    return filename, file_extension


def download_image(url: str, filename: str, folder: str = 'images/') -> str:
    """Функция для скачивания изображений"""
    path_to_download = os.path.join(folder, str(filename))

    response = get_request(url)

    Path(folder).mkdir(parents=True, exist_ok=True)
    with open(f"{path_to_download}{get_filename_and_file_extension(url)[1]}", 'wb') as file:
        file.write(response.content)

    return f"{path_to_download}.txt"


def parse_book_page(content) -> dict:
    """Возвращаем словарь с данными о книге: название, автор, ссылка на фото, список комментариев, список жанров"""
    title_tag = content.find('h1')
    book_title, book_author = [text.strip() for text in title_tag.text.strip().split("::")]

    all_comments = []
    all_genres = []
    genre_tag = content.find('span', class_='d_book').find_all('a')
    for genre in genre_tag:
        all_genres.append(genre.text)
    comment_tag = content.find_all('div', class_='texts')
    for comment in comment_tag:
        all_comments.append(comment.find('span').text)

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


def get_book_info(book_id: int) -> dict:
    """Парсим страницу книги и вовзращаем словарь с данными о книге"""
    url = f'https://tululu.org/b{book_id}/'
    response = get_request(url)
    soup = BeautifulSoup(response.text, 'lxml')
    return parse_book_page(soup)


for book_id in range(1, 11):
    url = f"https://tululu.org/txt.php?id={book_id}"
    try:
        book_info = get_book_info(book_id)
        # download_txt(url, f"{book_id}. {title}")
        # filename = get_filename_and_file_extension(image)[0]
        # download_image(image, filename)
        print(book_info.get('title'))
        print(book_info.get('genres'))
    except requests.exceptions.HTTPError:
        continue
