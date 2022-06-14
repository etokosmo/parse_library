import argparse
import json
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PAGE_PATH = os.path.join(BASE_DIR, 'pages')
BOOKS_ON_PAGE = 10
BOOKS_ON_ROW = 2


def get_arguments() -> argparse.Namespace:
    """Принимает аргументы из консоли"""
    parser = argparse.ArgumentParser(description='Верстка библиотеки')
    parser.add_argument(
        '--media_folder',
        help='Указать свой путь к медиа файлам с результатами',
        default='media'
    )
    parser.add_argument(
        '--json_path',
        help='Указать свой путь к *.json файлу с результатами',
        default='media'
    )
    return parser.parse_args()


def on_reload(arguments: argparse.Namespace) -> None:
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('template.html')

    with open(f"{arguments.json_path}/books.json", "r",
              encoding="utf8") as file_with_books:
        books = json.load(file_with_books)

    books_on_page = list(chunked(books, BOOKS_ON_PAGE))

    Path(PAGE_PATH).mkdir(parents=True, exist_ok=True)
    count_of_pages = len(books_on_page)
    for number, books in enumerate(books_on_page, start=1):
        chunked_books = list(chunked(books, BOOKS_ON_ROW))
        rendered_page = template.render(
            chunked_books=chunked_books,
            count_of_pages=count_of_pages,
            current_page=number,
        )

        with open(f'{PAGE_PATH}/index{number}.html', 'w',
                  encoding="utf8") as file:
            file.write(rendered_page)


def main():
    args = get_arguments()
    on_reload(args)

    server = Server()
    server.watch('template.html', on_reload)
    server.serve(root='.')


if __name__ == "__main__":
    main()
