import json
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PAGE_PATH = os.path.join(BASE_DIR, 'pages')


def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('template.html')

    with open("books.json", "r", encoding="utf8") as file_with_books:
        books_json = file_with_books.read()

    books = json.loads(books_json)
    books_on_page = list(chunked(books, 10))

    Path(PAGE_PATH).mkdir(parents=True, exist_ok=True)
    count_of_pages = len(books_on_page)
    for number, books in enumerate(books_on_page, start=1):
        chunked_books = list(chunked(books, 2))
        rendered_page = template.render(
            chunked_books=chunked_books,
            count_of_pages=count_of_pages,
            current_page=number,
        )

        with open(f'{PAGE_PATH}/index{number}.html', 'w',
                  encoding="utf8") as file:
            file.write(rendered_page)
        if number == 1:
            with open('index.html', 'w', encoding="utf8") as file:
                file.write(rendered_page)


def main():
    on_reload()

    server = Server()
    server.watch('template.html', on_reload)
    server.serve(root='.')


if __name__ == "__main__":
    main()
