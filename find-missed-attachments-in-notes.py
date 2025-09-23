import os
import re

# путь к Obsidian vault
VAULT_PATH = "/path/to/your/vault"
ATTACH_DIR = os.path.join(VAULT_PATH, "attachments")

# Собираем список всех файлов в attachments
attachments = set()
for root, dirs, files in os.walk(ATTACH_DIR):
    dirs[:] = [d for d in dirs if d not in [".obsidian", ".trash"]]
    for file in files:
        # игнорируем системные и нежелательные файлы
        if file in [".DS_Store"] or file.endswith((".base", ".canvas")):
            continue
        attachments.add(file)  # сохраняем только имя файла

# Регулярка для поиска [[...]] и ![[...]]
pattern = re.compile(r'!?\[\[([^\]]+)\]\]')

broken_links = {}

def strip_frontmatter(content: str) -> str:
    """
    Убирает блок frontmatter (--- ... ---) из начала заметки, если он есть.
    """
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2]  # возвращаем всё, что после второго ---
    return content

# Обходим все заметки
for root, dirs, files in os.walk(VAULT_PATH):
    dirs[:] = [d for d in dirs if d not in [".obsidian", ".trash"]]

    for file in files:
        # игнорируем системные и нежелательные файлы
        if file in [".DS_Store"] or file.endswith((".base", ".canvas")) or not file.endswith(".md"):
            continue

        note_path = os.path.join(root, file)
        with open(note_path, "r", encoding="utf-8") as f:
            content = f.read()

        # убираем frontmatter
        content = strip_frontmatter(content)

        found = set(pattern.findall(content))

        for ref in found:
            ref = ref.strip()

            # Убираем всё после "|" (например: image.png|300)
            if "|" in ref:
                ref = ref.split("|", 1)[0].strip()

            # Игнорируем WikiLinks (без расширения)
            if "." not in ref:
                continue

            # Игнорируем ссылки на .base и .canvas
            if ref.endswith((".base", ".canvas")):
                continue

            # Если ссылка есть в attachments — ок
            if ref in attachments:
                continue

            # Если точного совпадения нет → битая ссылка
            broken_links.setdefault(note_path, []).append(ref)

# Вывод результатов
if broken_links:
    print("Заметки с битым ссылками на вложения:\n")
    for note, refs in broken_links.items():
        print(f"{note}:")
        for r in refs:
            print(f"  - {r}")
else:
    print("Битых ссылок не найдено 🎉")

