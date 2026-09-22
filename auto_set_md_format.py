import os
import re
from datetime import datetime


def add_line_to_markdown_files(directory='.'):
    """
    Добавляет строку в начало всех Markdown файлов в указанной директории.

    :param line_to_add: Строка, которую нужно добавить.
    :param directory: Директория для поиска файлов (по умолчанию текущая директория).
    """
    # Получаем список всех файлов в указанной директории
    files = os.listdir(directory)

    # Проходимся по каждому файлу
    for filename in files:
        # Проверяем, что файл имеет расширение .md
        if filename.endswith('.md'):
            file_path = os.path.join(directory, filename)

            # Читаем содержимое файла
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.readlines()

            # Переменная для хранения всех найденных тегов
            tags = []
            for line in content:
                tags.extend(re.findall(r'#\w+', line))

            creation_time = os.stat(file_path).st_birthtime
            creation_date = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%dT%H:%M')

            formated_tag_list = ""
            for tag in tags:
                formated_tag_list += f"\n - {tag[1:]}"

            line_to_add = f"""---
created: {creation_date}
tags:{formated_tag_list}
project:
---
"""

            # Добавляем новую строку в начало файла
            content.insert(0, line_to_add + '\n')

            # Записываем обновленное содержимое обратно в файл
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(content)

            print(f"Добавлено в файл: {filename}, с тегами: {tags}")


if __name__ == "__main__":
    # Пример использования
    add_line_to_markdown_files()
