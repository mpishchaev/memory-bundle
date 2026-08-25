#!/usr/bin/env python3
"""Регенерация авто-секций _index.md по всему хранилищу.

Каждый каталог памяти содержит _index.md со статическим описанием и
авто-секцией между маркерами INDEX:AUTO. Этот скрипт пересчитывает
статистику (число .md файлов, подпапки) и перезаписывает ТОЛЬКО
авто-секцию — статический текст не трогается.

Чистый stdlib — запускается любым Python 3, без зависимостей.

Корень хранилища берётся из --root, иначе из BRAIN_ROOT, иначе
вычисляется как родительская папка каталога скриптов (05_Scripts/..).

    python update_indexes.py --root /путь/к/хранилищу
    python update_indexes.py --dry-run

Вызывается также из sleep_cycle/run.py и maintenance/check.py через
функцию update_all_indexes().
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
from pathlib import Path

DEFAULT_ROOT = Path(os.environ.get("BRAIN_ROOT", Path(__file__).resolve().parent.parent))

# Шумные подпапки — не обходим и не считаем (иначе 06_Skills/05_Scripts
# нахватают .md из node_modules / venv). Также пропускаются все dot-папки.
IGNORE_DIRS = {".venv", "node_modules", "__pycache__", "graphify-out"}

INDEX_NAME = "_index.md"

AUTO_START = (
    "<!-- INDEX:AUTO START — сгенерировано 05_Scripts/update_indexes.py, "
    "не редактировать вручную -->"
)
AUTO_END = "<!-- INDEX:AUTO END -->"
AUTO_RE = re.compile(r"<!-- INDEX:AUTO START.*?<!-- INDEX:AUTO END -->", re.DOTALL)


def _ignored(name: str) -> bool:
    return name in IGNORE_DIRS or name.startswith(".")


def count_md(directory: Path) -> int:
    """Рекурсивно считает .md файлы под directory, исключая _index.md,
    README.md и шумные подпапки."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        dirnames[:] = [d for d in dirnames if not _ignored(d)]
        for fn in filenames:
            low = fn.lower()
            if low.endswith(".md") and low not in (INDEX_NAME, "readme.md"):
                total += 1
    return total


def subdirs(directory: Path) -> list[Path]:
    """Непосредственные подпапки directory, без шумных."""
    return sorted(
        (p for p in directory.iterdir() if p.is_dir() and not _ignored(p.name)),
        key=lambda p: p.name,
    )


def find_indexes(root: Path) -> list[Path]:
    """Все _index.md в хранилище (шумные подпапки пропускаются)."""
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not _ignored(d)]
        if any(f.lower() == INDEX_NAME for f in filenames):
            found.append(Path(dirpath) / INDEX_NAME)
    return sorted(found)


def build_block(directory: Path) -> str:
    """Содержимое авто-секции для _index.md каталога directory."""
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [AUTO_START, "", f"_Обновлено: {now}_", ""]
    subs = subdirs(directory)
    if subs:
        lines.append("| Подпапка | .md файлов |")
        lines.append("|---|---|")
        for sd in subs:
            lines.append(f"| `{sd.name}/` | {count_md(sd)} |")
        lines.append("")
    lines.append(f"**Всего .md в каталоге:** {count_md(directory)}")
    lines.append(AUTO_END)
    return "\n".join(lines)


def update_index(index_path: Path, dry_run: bool = False) -> bool:
    """Перегенерирует авто-секцию одного _index.md. True — если файл изменён."""
    text = index_path.read_text(encoding="utf-8")
    block = build_block(index_path.parent)
    if AUTO_RE.search(text):
        new_text = AUTO_RE.sub(lambda _m: block, text)
    else:
        new_text = text.rstrip() + "\n\n" + block + "\n"
    if new_text == text:
        return False
    if not dry_run:
        index_path.write_text(new_text, encoding="utf-8")
    return True


def update_all_indexes(root: Path | str = DEFAULT_ROOT, dry_run: bool = False) -> int:
    """Обновляет все _index.md под root. Возвращает число изменённых файлов."""
    root = Path(root)
    return sum(update_index(idx, dry_run=dry_run) for idx in find_indexes(root))


def main() -> int:
    parser = argparse.ArgumentParser(description="Регенерация авто-секций _index.md.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    indexes = find_indexes(args.root)
    print(f"[update_indexes] Найдено {len(indexes)} файлов _index.md.")
    changed = 0
    for idx in indexes:
        if update_index(idx, dry_run=args.dry_run):
            changed += 1
            mark = "[dry-run] " if args.dry_run else ""
            print(f"  {mark}✓ {idx.relative_to(args.root)}")
    verb = "Будет обновлено" if args.dry_run else "Обновлено"
    print(f"[update_indexes] {verb}: {changed}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
