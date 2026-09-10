#!/usr/bin/env python3
"""
Move `tags` and `project` out of YAML frontmatter into the note body.

For every Markdown note that starts with a YAML frontmatter block, this removes
the `tags:` and `project:` keys from the frontmatter and re-inserts them right
after it, separated by one blank line:

  Было:
  ---
  created: 2026-06-22T11:15:29
  tags: _tech unix vpn
  project: [[✱ Official VPN]]
  ---

  Стало:
  ---
  created: 2026-06-22T11:15:29
  ---

  [[✱ Official VPN]]
  #_tech #unix #vpn

Rules:
  - `project` value is written as-is (surrounding quotes stripped); the project
    line comes first.
  - each `tags` token gets a leading `#` (tokens that already have one are kept).
  - empty `tags:` / `project:` (blank or `[]`) are just removed, nothing emitted.
  - if nothing is left in the frontmatter, the `---` block is removed entirely.
  - exactly one blank line separates the moved block from the note body.

Usage:
  frontmatter-tags-to-body.py        — preview affected files (dry run)
  frontmatter-tags-to-body.py -y     — apply changes
"""

import argparse
from pathlib import Path

VAULT = Path("/Users/k.fazilov/Second Brain")
SKIP_DIRS = {"Attachments", "Templates", "Canvas", "Templates"}

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


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1].strip()
    return value


def _format_tags(value: str) -> str:
    """'_tech #unix vpn' -> '#_tech #unix #vpn'. Returns '' if no real tokens."""
    tokens = ["#" + t.lstrip("#") for t in value.split() if t.strip("#")]
    return " ".join(tokens)


def transform_content(content: str) -> tuple[str, bool]:
    """Move frontmatter `tags`/`project` into the body. Returns (new_content, changed)."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return content, False

    close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if close is None:
        return content, False

    fm = lines[1:close]
    body = lines[close + 1:]

    fm_kept: list[str] = []
    project_line = ""
    tags_line = ""
    found = False

    for line in fm:
        if line.startswith("project:"):
            found = True
            value = _strip_quotes(line[len("project:"):].strip())
            if value not in ("", "[]"):
                project_line = value
        elif line.startswith("tags:"):
            found = True
            value = line[len("tags:"):].strip()
            if value not in ("", "[]"):
                tags_line = _format_tags(value)
        else:
            fm_kept.append(line)

    if not found:
        return content, False

    frontmatter_block = ""
    if any(line.strip() for line in fm_kept):
        frontmatter_block = "---\n" + "\n".join(fm_kept).strip("\n") + "\n---\n"

    moved = "\n".join(part for part in (project_line, tags_line) if part)
    body_text = "\n".join(body).lstrip("\n").rstrip("\n")

    out = frontmatter_block
    if moved:
        out += ("\n" if frontmatter_block else "") + moved + "\n"
    if body_text:
        out += ("\n" if out else "") + body_text + "\n"

    if content.endswith("\n") and not out.endswith("\n"):
        out += "\n"
    if not content.endswith("\n") and out.endswith("\n"):
        out = out[:-1]

    return out, out != content


def _frontmatter_region(text: str, extra: int = 3) -> str:
    """First few lines through the frontmatter close (+ a little body) for previews."""
    lines = text.splitlines()
    end = len(lines)
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i + 1
                break
    return "\n".join(lines[:end + extra])


def main():
    parser = argparse.ArgumentParser(
        description="Move `tags` and `project` from YAML frontmatter into the note body",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("-y", "--yes", action="store_true",
                        help="Apply changes (default is a dry run)")
    args = parser.parse_args()

    to_update = []
    for f in iter_md_files():
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        _, changed = transform_content(content)
        if changed:
            to_update.append(f)

    if not to_update:
        print(yellow("\nNo files need changes.\n"))
        return

    print(bold(f"\n{len(to_update)} files to update:\n"))
    for f in to_update:
        print(f"  {f.name}")

    if not args.yes:
        print(bold("\nPreview (first 3):\n"))
        for f in to_update[:3]:
            content = f.read_text(encoding="utf-8", errors="ignore")
            new_content, _ = transform_content(content)
            print(cyan(f"  {f.name}"))
            print(dim("  --- before ---"))
            print("\n".join(f"  {ln}" for ln in _frontmatter_region(content).splitlines()))
            print(dim("  --- after ---"))
            print("\n".join(f"  {ln}" for ln in _frontmatter_region(new_content).splitlines()))
            print()
        print(dim(f"Dry run — no files changed. Add -y to apply.\n"))
        return

    print()
    updated = 0
    errors = 0
    for f in to_update:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            new_content, changed = transform_content(content)
            if changed:
                f.write_text(new_content, encoding="utf-8")
                updated += 1
        except OSError as e:
            print(red(f"  Error updating {f.name}: {e}"))
            errors += 1

    print(green(bold(f"Done: {updated} files updated")) + (red(f", {errors} errors") if errors else "") + "\n")


if __name__ == "__main__":
    main()
