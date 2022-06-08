import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PAGE_PATH = os.path.join(BASE_DIR, 'pages')
BOOKS_ON_PAGE = 10
BOOKS_ON_ROW = 2


@dataclass
class ParseArgs:
    media_folder: str
    json_path: str


def get_arguments() -> ParseArgs:
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
    args = parser.parse_args()
    parse_args = ParseArgs(
        media_folder=args.media_folder,
        json_path=args.json_path
    )
    return parse_args


def on_reload(arguments: ParseArgs):
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('template.html')

    with open(f"{arguments.json_path}/books.json", "r",
              encoding="utf8") as file_with_books:
        books_json = file_with_books.read()

    books = json.loads(books_json)
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
