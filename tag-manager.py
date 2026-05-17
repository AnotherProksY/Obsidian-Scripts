#!/usr/bin/env python3
"""
Tag manager for Markdown knowledge base.

Usage:
  tag-manager.py list                    — show all tags with file counts
  tag-manager.py search <tag>            — show files containing tag
  tag-manager.py rename <old> <new>      — preview rename (dry run)
  tag-manager.py rename <old> <new> -y  — apply rename

Examples:
  tag-manager.py list
  tag-manager.py search #health
  tag-manager.py rename #health #_health
  tag-manager.py rename #health #_health -y
"""

import sys
import re
import argparse
from pathlib import Path
from collections import defaultdict

VAULT = Path("/Users/k.fazilov/Library/Mobile Documents/27N4MQEA55~pro~writer/Documents")
SKIP_DIRS = {"attachments", "Templates"}

# Terminal colors
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[31m"
    GREEN  = "\033[32m"
    YELLOW = "\033[33m"
    CYAN   = "\033[36m"


def bold(s):   return f"{C.BOLD}{s}{C.RESET}"
def dim(s):    return f"{C.DIM}{s}{C.RESET}"
def green(s):  return f"{C.GREEN}{s}{C.RESET}"
def yellow(s): return f"{C.YELLOW}{s}{C.RESET}"
def cyan(s):   return f"{C.CYAN}{s}{C.RESET}"
def red(s):    return f"{C.RED}{s}{C.RESET}"


def iter_md_files():
    for f in sorted(VAULT.glob("*.md")):
        yield f
    for f in sorted(VAULT.rglob("*.md")):
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        if f.parent == VAULT:
            continue
        yield f


def parse_tags_from_line(line: str) -> list[str]:
    """Extract tags from a 'tags: #foo #bar' line."""
    value = line[len("tags:"):].strip()
    if not value or value in ("[]", ""):
        return []
    return [t for t in value.split() if t.startswith("#")]


def get_tags_line(content: str) -> tuple[int, str] | tuple[None, None]:
    """Return (line_index, line_text) of the tags line in frontmatter, or (None, None)."""
    lines = content.splitlines()
    in_frontmatter = False
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            continue
        if in_frontmatter and line.strip() == "---":
            break
        if in_frontmatter and line.startswith("tags:"):
            return i, line
    return None, None


def cmd_list():
    tag_counts = defaultdict(int)

    for f in iter_md_files():
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        _, tags_line = get_tags_line(content)
        if tags_line is None:
            continue
        for tag in parse_tags_from_line(tags_line):
            tag_counts[tag] += 1

    if not tag_counts:
        print("No tags found.")
        return

    sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])
    max_count_width = len(str(sorted_tags[0][1]))

    print(bold(f"\n{'Count':>{max_count_width}}  Tag"))
    print("─" * (max_count_width + 20))
    for tag, count in sorted_tags:
        print(f"{cyan(str(count).rjust(max_count_width))}  {tag}")
    print(dim(f"\n{len(sorted_tags)} unique tags across vault\n"))


def cmd_search(tag: str):
    if not tag.startswith("#"):
        tag = "#" + tag

    matches = []
    for f in iter_md_files():
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        _, tags_line = get_tags_line(content)
        if tags_line is None:
            continue
        if tag in parse_tags_from_line(tags_line):
            matches.append(f)

    if not matches:
        print(yellow(f"\nNo files found with tag {tag}\n"))
        return

    print(bold(f"\nFiles with tag {cyan(tag)} ({len(matches)} total):\n"))
    for f in matches:
        print(f"  {f.name}")
    print()


def rename_tag_in_content(content: str, old_tag: str, new_tag: str) -> tuple[str, bool]:
    """Replace old_tag with new_tag in the tags frontmatter line. Returns (new_content, changed)."""
    line_idx, tags_line = get_tags_line(content)
    if tags_line is None:
        return content, False

    tags = parse_tags_from_line(tags_line)
    if old_tag not in tags:
        return content, False

    new_tags = [new_tag if t == old_tag else t for t in tags]
    new_tags_line = "tags: " + " ".join(new_tags)

    lines = content.splitlines(keepends=True)
    # Preserve original line ending
    original_line = lines[line_idx]
    ending = "\n" if original_line.endswith("\n") else ""
    lines[line_idx] = new_tags_line + ending

    return "".join(lines), True


def cmd_rename(old_tag: str, new_tag: str, apply: bool):
    if not old_tag.startswith("#"):
        old_tag = "#" + old_tag
    if not new_tag.startswith("#"):
        new_tag = "#" + new_tag

    if old_tag == new_tag:
        print(red("Old and new tags are the same. Nothing to do."))
        sys.exit(1)

    to_update = []
    for f in iter_md_files():
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        _, new_content_changed = rename_tag_in_content(content, old_tag, new_tag)
        if new_content_changed:
            to_update.append(f)

    if not to_update:
        print(yellow(f"\nNo files found with tag {old_tag}\n"))
        return

    arrow = f"{cyan(old_tag)} → {green(new_tag)}"
    print(bold(f"\nRename {arrow} ({len(to_update)} files):\n"))
    for f in to_update:
        print(f"  {f.name}")

    if not apply:
        print(dim(f"\nDry run — no files changed. Add -y to apply.\n"))
        return

    print()
    updated = 0
    errors = 0
    for f in to_update:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            new_content, changed = rename_tag_in_content(content, old_tag, new_tag)
            if changed:
                f.write_text(new_content, encoding="utf-8")
                updated += 1
        except OSError as e:
            print(red(f"  Error updating {f.name}: {e}"))
            errors += 1

    print(green(bold(f"Done: {updated} files updated")) + (red(f", {errors} errors") if errors else "") + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Tag manager for Markdown knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    subparsers.add_parser("list", help="Show all tags with file counts")

    p_search = subparsers.add_parser("search", help="Show files with a given tag")
    p_search.add_argument("tag", help="Tag to search (e.g. #health or health)")

    p_rename = subparsers.add_parser("rename", help="Rename a tag across all files")
    p_rename.add_argument("old_tag", help="Current tag name (e.g. #health)")
    p_rename.add_argument("new_tag", help="New tag name (e.g. #_health)")
    p_rename.add_argument("-y", "--yes", action="store_true", help="Apply changes (default is dry run)")

    args = parser.parse_args()

    if args.cmd == "list":
        cmd_list()
    elif args.cmd == "search":
        cmd_search(args.tag)
    elif args.cmd == "rename":
        cmd_rename(args.old_tag, args.new_tag, apply=args.yes)


if __name__ == "__main__":
    main()
