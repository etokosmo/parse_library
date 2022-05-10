from pathlib import Path

import requests

PATH_TO_DOWNLOAD = "books"
Path(PATH_TO_DOWNLOAD).mkdir(parents=True, exist_ok=True)

for book_id in range(1, 11):
    url = f"https://tululu.org/txt.php?id={book_id}"
    response = requests.get(url)
    response.raise_for_status()
    filename = f"{PATH_TO_DOWNLOAD}/id{book_id}.txt"
    with open(filename, 'wb') as file:
        file.write(response.content)
