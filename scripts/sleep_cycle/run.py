"""CLI entry point: orchestrate Raw → Wiki consolidation (v2)."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from sleep_cycle.dedup import find_match, index_wiki
    from sleep_cycle.extractor import CATEGORIES, extract_concepts
    from sleep_cycle.loader import load_raw_notes
    from sleep_cycle.writer import (
        add_source_backlink,
        append_concept,
        append_inbox,
        append_log,
        create_concept,
        create_source,
        mark_raw_consolidated,
    )
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from .dedup import find_match, index_wiki
    from .extractor import CATEGORIES, extract_concepts
    from .loader import load_raw_notes
    from .writer import (
        add_source_backlink,
        append_concept,
        append_inbox,
        append_log,
        create_concept,
        create_source,
        mark_raw_consolidated,
    )

# update_indexes лежит в 05_Scripts/ (на sys.path после блока выше).
from update_indexes import update_all_indexes


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sleep Cycle: Raw → Wiki consolidation (v2 two-pass).")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--archive", action="store_true")
    p.add_argument("--graphify", action="store_true")
    p.add_argument("--root", type=Path, default=None)
    return p.parse_args()


def _titles_by_category(entries) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for e in entries:
        cat = e.path.parent.name if e.path.parent.name in CATEGORIES else "concepts"
        out[cat].append(e.title)
    return dict(out)


def main() -> int:
    load_dotenv(Path(__file__).resolve().parent / ".env")
    args = parse_args()

    root = args.root or Path(os.environ.get("BRAIN_ROOT", Path(__file__).resolve().parent.parent.parent))
    raw_dir = root / "00_Raw"
    wiki_dir = root / "01_Wiki"
    archive_dir = root / "04_Archive"
    log_path = root / "03_Meta/Log.md"
    inbox_path = root / "03_Meta/Inbox_Concepts.md"

    notes = load_raw_notes(raw_dir, limit=args.limit)
    if not notes:
        msg = "[Sleep Cycle] Нет новых данных для консолидации."
        print(msg)
        if not args.dry_run:
            append_log(log_path, msg)
        return 0

    wiki_entries = index_wiki(wiki_dir)
    titles_by_cat = _titles_by_category(wiki_entries)
    total = sum(len(v) for v in titles_by_cat.values())
    print(f"[Sleep Cycle v2] К обработке: {len(notes)} заметок. Вики содержит {total} концептов в {len(titles_by_cat)} категориях.")

    created: list[tuple[str, str]] = []  # (title, category)
    appended: list[str] = []

    for note in notes:
        rel = note.path.relative_to(root)
        print(f"\n→ {rel}")
        if args.dry_run:
            print(f"    [dry-run] {note.title!r}, {len(note.body)} chars")
            continue
        try:
            concepts = extract_concepts(
                raw_title=note.title,
                raw_body=note.body,
                wiki_titles_by_cat=titles_by_cat,
                brain_root=root,
            )
        except Exception as exc:
            print(f"    ✗ extractor error: {exc}")
            continue

        batch_concept_paths: list[Path] = []
        batch_concept_titles: list[str] = []
        for concept in concepts:
            match = find_match(concept.title, wiki_entries)
            if match:
                append_concept(match.path, concept)
                appended.append(concept.title)
                batch_concept_paths.append(match.path)
                batch_concept_titles.append(concept.title)
                print(f"    + append → {match.path.relative_to(wiki_dir)}")
            else:
                path = create_concept(wiki_dir, concept)
                created.append((concept.title, concept.category))
                batch_concept_paths.append(path)
                batch_concept_titles.append(concept.title)
                wiki_entries = index_wiki(wiki_dir)
                titles_by_cat = _titles_by_category(wiki_entries)
                print(f"    + create → {path.relative_to(wiki_dir)}")

        if note.urls and batch_concept_titles:
            source_path = create_source(
                wiki_dir,
                raw_path=note.path,
                raw_title=note.title,
                urls=note.urls,
                concept_titles=batch_concept_titles,
            )
            source_title = source_path.stem.replace("_", " ")
            for cp in batch_concept_paths:
                add_source_backlink(cp, source_title)
            print(f"    ↪ source → sources/{source_path.name} ({len(note.urls)} URLs)")

        mark_raw_consolidated(note.path, archive_dir if args.archive else None)

    if args.dry_run:
        print(f"\n[dry-run] Plan complete. Would process {len(notes)} files.")
        return 0

    if created:
        append_inbox(inbox_path, created)

    summary = (
        f"[Sleep Cycle] Обработано {len(notes)} заметок. "
        f"Создано: {len(created)} ({', '.join(f'[[{t}]]' for t, _ in created) or '—'}). "
        f"Дополнено: {len(appended)}."
    )
    append_log(log_path, summary)
    print(f"\n✓ {summary}")

    n_idx = update_all_indexes(root)
    print(f"[Sleep Cycle] Обновлено авто-секций _index.md: {n_idx}.")

    if args.graphify:
        print("[Sleep Cycle] graphify update .")
        subprocess.run(["graphify", "update", "."], cwd=root, check=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
