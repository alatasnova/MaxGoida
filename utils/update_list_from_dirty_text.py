import os
import re
import tkinter as tk
from urllib.parse import urlparse
root = tk.Tk()

def extract_links(text: str) -> list:
    """
    Извлекает все валидные URL из текста.
    """
    if not text:
        return []

    # Регулярное выражение для поиска URL (поддерживает http, https, ftp)
    # Это расширенный паттерн, который ищет начало протокола и корректные символы до пробела/кавычки
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'

    # Находим все совпадения
    raw_links = re.findall(url_pattern, text)

    valid_links = []

    for link in raw_links:
        # Убираем лишние знаки препинания в конце, которые могли попасть в захват (точки, запятые, скобки)
        link = link.strip('.,!?;:) ]')

        # Если ссылка начинается с www., добавляем протокол для проверки валидности
        if link.lower().startswith('www.'):
            link = 'http://' + link

        # Проверяем, является ли найденная строка валидным URL через urlparse
        parsed = urlparse(link)
        if parsed.scheme and parsed.netloc:
            valid_links.append(link)

    return valid_links


def add_source_url(new_url, filename="../sources.txt"):
    """
    Добавляет URL в файл, если его там еще нет.
    """
    # Убираем пробелы и переносы строк по краям новой ссылки
    new_url = new_url.strip()

    # Если строка пустая, ничего не делаем
    if not new_url:
        print("Ошибка: URL пустой")
        return False

    # Проверяем, существует ли файл. Если нет — создаем пустой.
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_url + '\n')
        print(f"Файл создан. Добавлена ссылка: {new_url}")
        return True

    # Читаем существующие ссылки
    with open(filename, 'r', encoding='utf-8') as f:
        # Читаем все строки, убираем пробелы и фильтруем пустые строки
        existing_urls = {line.strip() for line in f if line.strip()}

    # Проверяем, есть ли уже такая ссылка
    if new_url in existing_urls:
        print(f"Пропуск: Ссылка уже существует в файле: {new_url}")
        return False
    else:
        # Добавляем в конец файла
        # Открываем в режиме 'a' (append)
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(new_url + '\n')
        print(f"Успешно добавлено: {new_url}")
        return True

text = root.clipboard_get()
links = extract_links(text)

for link in links:
    add_source_url(link)