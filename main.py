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


def download_txt(url: str, filename: str, folder: str='books/') -> str:
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


def download_image(url: str, filename: str, folder: str='images/') -> str:
    """Функция для скачивания изображений"""
    path_to_download = os.path.join(folder, str(filename))

    response = get_request(url)

    Path(folder).mkdir(parents=True, exist_ok=True)
    with open(f"{path_to_download}{get_filename_and_file_extension(url)[1]}", 'wb') as file:
        file.write(response.content)

    return f"{path_to_download}.txt"


def get_book_info(book_id: int) -> Tuple[str, str, str, list]:
    """Получаем название, автора и ссылку на книгу"""
    url = f'https://tululu.org/b{book_id}/'

    response = get_request(url)

    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('h1')
    all_comments = []
    comments = soup.find_all('div', class_='texts')
    for comment in comments:
        all_comments.append(comment.find('span').text)
    book_image = soup.find('div', class_='bookimage').find('img')['src']
    book_image = urljoin('https://tululu.org/', book_image)
    title, author = [text.strip() for text in title_tag.text.strip().split("::")]
    return title, author, book_image, all_comments


for book_id in range(1, 11):
    url = f"https://tululu.org/txt.php?id={book_id}"
    try:
        title, author, image, comments = get_book_info(book_id)
        # download_txt(url, f"{book_id}. {title}")
        # filename = get_filename_and_file_extension(image)[0]
        # download_image(image, filename)
        print(title)
        print(*comments, sep='\n')
    except requests.exceptions.HTTPError:
        continue
