import os

# путь к Obsidian vault
VAULT_PATH = "/path/to/your/vault"

attachments = []
notes = []

# Собираем все файлы
for root, dirs, files in os.walk(VAULT_PATH):
    # убираем служебные директории
    dirs[:] = [d for d in dirs if d not in [".obsidian", ".trash"]]

    for file in files:
        # игнорируем лишние файлы
        if file == ".DS_Store" or file.endswith(".base"):
            continue

        full_path = os.path.join(root, file)
        rel_path = os.path.relpath(full_path, VAULT_PATH)

        if file.endswith(".md"):
            notes.append(full_path)
        else:
            attachments.append(rel_path.replace("\\", "/"))  # нормализуем слеши

# Читаем все заметки и собираем их содержимое
all_notes_text = ""
for note in notes:
    with open(note, "r", encoding="utf-8") as f:
        all_notes_text += f.read() + "\n"

# Ищем неиспользуемые вложения
unused_attachments = []
for attachment in attachments:
    filename = os.path.basename(attachment)
    if filename not in all_notes_text:
        unused_attachments.append(attachment)

print("Найдено неиспользуемых вложений:", len(unused_attachments))
for f in unused_attachments:
    print(f)

