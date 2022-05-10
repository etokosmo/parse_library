import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pathvalidate import is_valid_filename, sanitize_filename

PATH_TO_DOWNLOAD = "books"
Path(PATH_TO_DOWNLOAD).mkdir(parents=True, exist_ok=True)


def check_for_redirect(response: requests.models.Response):
    if response.history:
        raise requests.HTTPError


def download_txt(url, filename, folder='books/'):
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

    response = requests.get(url)
    check_for_redirect(response)
    response.raise_for_status()
    Path(folder).mkdir(parents=True, exist_ok=True)
    with open(f"{path_to_download}.txt", 'wb') as file:
        file.write(response.content)

    return f"{path_to_download}.txt"


def get_title_and_author(book_id):
    url = f'https://tululu.org/b{book_id}/'
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('h1')
    title, author = [text.strip() for text in title_tag.text.strip().split("::")]
    return title, author


for book_id in range(1, 11):
    url = f"https://tululu.org/txt.php?id={book_id}"
    try:
        title, author = get_title_and_author(book_id)
        download_txt(url, f"{book_id}. {title}")
    except requests.exceptions.HTTPError:
        continue
