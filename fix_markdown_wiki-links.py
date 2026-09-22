#!/usr/bin/env python3
"""
Скрипт для добавления обратных ссылок на подчиненные заметки.
Ищет в project: ссылку на родительскую заметку и добавляет список всех связанных заметок.
"""

import re
from pathlib import Path
from typing import Set, Optional, Tuple


def extract_frontmatter(content: str) -> Tuple[Optional[str], str]:
    """
    Извлекает YAML frontmatter из Markdown файла.
    
    Returns:
        Кортеж (frontmatter, остаток содержимого)
    """
    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not match:
        return None, content
    
    frontmatter = match.group(1)
    body = content[match.end():]
    return frontmatter, body


def extract_project_links(frontmatter: str) -> Set[str]:
    """
    Извлекает все Wiki-ссылки из поля project в frontmatter.
    
    Returns:
        Множество названий связанных заметок (без [[]])
    """
    if not frontmatter:
        return set()
    
    # Ищем строку project: и берем все wiki ссылки
    project_match = re.search(r'project:\s*(.+?)(?:\n[a-z]+:|$)', frontmatter, re.DOTALL)
    if not project_match:
        return set()
    
    project_content = project_match.group(1)
    
    # Извлекаем все [[...]] из project
    links = re.findall(r'\[\[([^\]]+)\]\]', project_content)
    return set(links)


def get_related_files(md_files: list, parent_name: str) -> list:
    """
    Находит все заметки, которые имеют project: [[parent_name]].
    
    Args:
        md_files: список всех .md файлов
        parent_name: название родительской заметки (без .md)
    
    Returns:
        Список названий связанных заметок
    """
    related = []
    
    for md_file in md_files:
        # Пропускаем саму родительскую заметку
        if md_file.stem == parent_name:
            continue
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            frontmatter, _ = extract_frontmatter(content)
            if not frontmatter:
                continue
            
            projects = extract_project_links(frontmatter)
            
            # Если в project указана наша родительская заметка, добавляем её в список
            if parent_name in projects:
                related.append(md_file.stem)
        
        except Exception as e:
            print(f'Ошибка при чтении {md_file}: {e}')
            continue
    
    return sorted(related)


def has_related_section(content: str) -> bool:
    """
    Проверяет, есть ли уже секция со связанными заметками.
    """
    return '## Связанные заметки' in content or '## Related notes' in content


def add_related_section(content: str, related_notes: list) -> str:
    """
    Добавляет или обновляет секцию со связанными заметками в конец файла.
    """
    if not related_notes:
        return content
    
    # Формируем список связанных заметок
    related_section = '\n## Связанные заметки\n\n'
    for note in related_notes:
        related_section += f'- [[{note}]]\n'
    
    # Если секция уже существует, заменяем её
    if has_related_section(content):
        # Удаляем старую секцию
        content = re.sub(
            r'\n## (?:Связанные заметки|Related notes)\n\n(?:- \[\[.+?\]\]\n)*',
            '',
            content,
            flags=re.MULTILINE
        )
    
    # Добавляем новую секцию в конец
    if not content.endswith('\n'):
        content += '\n'
    
    content += related_section
    return content


def process_markdown_file(file_path: Path, all_md_files: list) -> bool:
    """
    Обрабатывает один Markdown файл.
    Добавляет список всех связанных заметок.
    
    Returns:
        True если файл был изменен
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Получаем название заметки без расширения
        parent_name = file_path.stem
        
        # Находим все связанные заметки
        related_notes = get_related_files(all_md_files, parent_name)
        
        if not related_notes:
            return False
        
        # Добавляем или обновляем секцию
        new_content = add_related_section(content, related_notes)
        
        # Проверяем, изменился ли контент
        if new_content == original_content:
            return False
        
        # Записываем обратно
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    
    except Exception as e:
        print(f'Ошибка при обработке {file_path}: {e}')
        return False


def main():
    """Главная функция."""
    current_dir = Path('.')
    
    # Находим все .md файлы
    md_files = list(current_dir.glob('*.md'))
    
    if not md_files:
        print('Не найдено Markdown файлов в текущей директории')
        return
    
    print(f'Найдено {len(md_files)} Markdown файлов')
    print('=' * 60)
    
    modified_count = 0
    for md_file in md_files:
        if process_markdown_file(md_file, md_files):
            related = get_related_files(md_files, md_file.stem)
            print(f'✓ Обновлен: {md_file.name} ({len(related)} связанных заметок)')
            modified_count += 1
        else:
            print(f'- Без изменений: {md_file.name}')
    
    print('=' * 60)
    print(f'Всего обновлено файлов: {modified_count}/{len(md_files)}')


if __name__ == '__main__':
    main()

