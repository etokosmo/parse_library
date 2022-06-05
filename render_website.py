import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked

PAGE_PATH = './pages'


def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    with open("books.json", "r", encoding="utf8") as file_with_books:
        books_json = file_with_books.read()

    books = json.loads(books_json)
    books_on_page = list(chunked(books, 10))

    template = env.get_template('template.html')

    Path(PAGE_PATH).mkdir(parents=True, exist_ok=True)
    for number, books in enumerate(books_on_page, start=1):
        chunked_books = list(chunked(books, 2))
        print(chunked_books)
        rendered_page = template.render(
            chunked_books=chunked_books,
        )

        with open(f'{PAGE_PATH}/index{number}.html', 'w',
                  encoding="utf8") as file:
            file.write(rendered_page)


on_reload()

server = Server()

server.watch('template.html', on_reload)

server.serve(root='.')
