"""Merge a duplicate concept into a winner.

Steps:
1. Load winner + loser frontmatter.
2. Merge loser's aliases (plus loser's title itself) into winner's aliases.
3. Merge tags + category stays from winner.
4. If loser has body content beyond the standard skeleton, append it to
   winner under `## Слияние с [[loser title]]`.
5. Rewrite all `[[loser title]]` references in 01_Wiki/ and 03_Meta/ to
   `[[winner title]]`. (Aliases resolve automatically once added to winner.)
6. Remove loser title from 03_Meta/Inbox_Concepts.md if present.
7. git rm the loser file (or just delete and let git track).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

import frontmatter


def _read(path: Path) -> frontmatter.Post:
    return frontmatter.load(path)


def _write(path: Path, post: frontmatter.Post) -> None:
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")


def _title_of(post: frontmatter.Post, path: Path) -> str:
    return str(post.metadata.get("title") or path.stem.replace("_", " "))


def merge(winner_path: Path, loser_path: Path, dry_run: bool = False) -> dict:
    winner = _read(winner_path)
    loser = _read(loser_path)
    winner_title = _title_of(winner, winner_path)
    loser_title = _title_of(loser, loser_path)

    # 1. Merge aliases.
    win_aliases = set(winner.metadata.get("aliases") or [])
    win_aliases.update(loser.metadata.get("aliases") or [])
    win_aliases.add(loser_title)
    win_aliases.discard(winner_title)
    winner.metadata["aliases"] = sorted(win_aliases)

    # 2. Merge tags.
    win_tags = set(winner.metadata.get("tags") or [])
    win_tags.update(loser.metadata.get("tags") or [])
    winner.metadata["tags"] = sorted(win_tags)

    # 3. Append loser body section if it has substance.
    loser_body = (loser.content or "").strip()
    if loser_body and len(loser_body) > 50:
        winner.content = (winner.content or "").rstrip() + (
            f"\n\n## Слияние с [[{loser_title}]]\n\n{loser_body}\n"
        )

    if dry_run:
        print(f"[dry-run] would update aliases: {winner.metadata['aliases']}")
        print(f"[dry-run] would rewrite [[{loser_title}]] → [[{winner_title}]]")
        return {}

    _write(winner_path, winner)

    # 4. Rewrite wikilinks across vault.
    rewrite_count = 0
    root = winner_path.parent.parent.parent  # 01_Wiki/cat/file.md → root
    patterns = [
        re.compile(re.escape(f"[[{loser_title}]]")),
        re.compile(re.escape(f"[[{loser_title}|")),
    ]
    for md in list(root.rglob("*.md")):
        if md == loser_path:
            continue
        if any(part in ("graphify-out", "04_Archive", ".obsidian", ".venv") for part in md.parts):
            continue
        text = md.read_text(encoding="utf-8")
        before = text
        text = text.replace(f"[[{loser_title}]]", f"[[{winner_title}]]")
        text = text.replace(f"[[{loser_title}|", f"[[{winner_title}|")
        if text != before:
            md.write_text(text, encoding="utf-8")
            rewrite_count += 1

    # 5. Remove loser from Inbox_Concepts.md.
    inbox = root / "03_Meta/Inbox_Concepts.md"
    if inbox.exists():
        text = inbox.read_text(encoding="utf-8")
        new_text = re.sub(rf"^- \[\[{re.escape(loser_title)}\]\]\n?", "", text, flags=re.MULTILINE)
        if new_text != text:
            inbox.write_text(new_text, encoding="utf-8")

    # 6. Delete loser via git rm if tracked, else fs delete.
    try:
        subprocess.run(["git", "rm", "-f", str(loser_path)], check=True, cwd=root, capture_output=True)
    except subprocess.CalledProcessError:
        loser_path.unlink(missing_ok=True)

    return {"rewrites": rewrite_count, "winner": str(winner_path), "loser": str(loser_path)}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--winner", type=Path, required=True)
    p.add_argument("--loser", type=Path, required=True)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    result = merge(args.winner.resolve(), args.loser.resolve(), dry_run=args.dry_run)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
