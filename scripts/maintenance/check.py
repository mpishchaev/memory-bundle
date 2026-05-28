"""Vault health check: broken [[links]], orphan pages, malformed YAML.

Implements the vault-maintenance skill spec. Read-only by default;
appends a report to 03_Meta/Log.md when --report is passed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from update_indexes import update_all_indexes  # noqa: E402  (05_Scripts/ на sys.path)

LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
CODE_SPAN_RE = re.compile(r"`[^`]*`")
CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
REQUIRED_YAML = {"title", "tags", "status"}

# Wiki-links that intentionally point to non-file anchors (folder names, the
# protocol doc, the graphify tool). Excluded from broken-link reports.
KNOWN_ANCHORS = {
    "00_Raw",
    "01_Wiki",
    "02_Memory",
    "03_Meta",
    "04_Archive",
    "05_Scripts",
    "06_Skills",
    "AGENTS.md",
    "CLAUDE.md",
    "Graphify",
    "Obsidian",
    "Master_Index",
    "Log",
    "hot",
    "Inbox_Concepts",
}


def _all_md(root: Path, subdirs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for sub in subdirs:
        d = root / sub
        if d.exists():
            paths.extend(
                p for p in d.rglob("*.md")
                if p.name.lower() not in ("readme.md", "_index.md")
            )
    return paths


def _index_titles(paths: list[Path]) -> dict[str, Path]:
    idx: dict[str, Path] = {}
    for p in paths:
        try:
            post = frontmatter.load(p)
        except Exception:
            continue
        title = str(post.metadata.get("title") or p.stem.replace("_", " "))
        idx[title] = p
        idx[p.stem] = p
        idx[p.stem.replace("_", " ")] = p
        for alias in post.metadata.get("aliases") or []:
            idx[str(alias)] = p
    return idx


def run_check(root: Path) -> dict:
    wiki_paths = _all_md(root, ["01_Wiki", "02_Memory"])
    title_index = _index_titles(wiki_paths)

    bad_yaml: list[tuple[Path, list[str]]] = []
    broken: list[tuple[Path, str]] = []
    incoming: dict[Path, int] = defaultdict(int)

    for path in wiki_paths:
        try:
            post = frontmatter.load(path)
        except Exception as exc:
            bad_yaml.append((path, [f"parse error: {exc}"]))
            continue
        missing = sorted(REQUIRED_YAML - set(post.metadata.keys()))
        if missing:
            bad_yaml.append((path, [f"missing: {m}" for m in missing]))
        content = CODE_BLOCK_RE.sub("", post.content or "")
        content = CODE_SPAN_RE.sub("", content)
        for match in LINK_RE.finditer(content):
            target = match.group(1).strip()
            if target in KNOWN_ANCHORS:
                continue
            if target in title_index and title_index[target] != path:
                incoming[title_index[target]] += 1
            elif target not in title_index:
                broken.append((path, target))

    orphans = [p for p in wiki_paths if incoming[p] == 0]

    return {
        "scanned": len(wiki_paths),
        "bad_yaml": bad_yaml,
        "broken": broken,
        "orphans": orphans,
    }


def format_report(result: dict, root: Path) -> str:
    lines = [
        f"## Maintenance report {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- Просканировано файлов: {result['scanned']}",
        f"- Битых ссылок: {len(result['broken'])}",
        f"- Страниц-сирот: {len(result['orphans'])}",
        f"- С проблемами YAML: {len(result['bad_yaml'])}",
    ]
    if result["broken"]:
        lines.append("\n### Broken links")
        for src, target in result["broken"][:50]:
            lines.append(f"  - {src.relative_to(root)} → [[{target}]]")
    if result["orphans"]:
        lines.append("\n### Orphans")
        for p in result["orphans"][:50]:
            lines.append(f"  - {p.relative_to(root)}")
    if result["bad_yaml"]:
        lines.append("\n### YAML issues")
        for path, issues in result["bad_yaml"][:50]:
            lines.append(f"  - {path.relative_to(root)}: {', '.join(issues)}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Vault health check.")
    parser.add_argument("--root", type=Path, default=Path(os.environ.get("BRAIN_ROOT", Path(__file__).resolve().parent.parent.parent)))
    parser.add_argument("--report", action="store_true", help="Append report to 03_Meta/Log.md.")
    args = parser.parse_args()

    result = run_check(args.root)
    report = format_report(result, args.root)
    print(report)

    if args.report:
        log = args.root / "03_Meta/Log.md"
        with log.open("a", encoding="utf-8") as fh:
            fh.write("\n" + report + "\n")
        n_idx = update_all_indexes(args.root)
        print(f"[update_indexes] Обновлено авто-секций _index.md: {n_idx}.")

    return 0 if not result["broken"] and not result["bad_yaml"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
