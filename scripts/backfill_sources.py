"""Backfill 01_Wiki/sources/ from existing 00_Raw notes.

For each raw note that contains URLs:
  1. Create a source note in 01_Wiki/sources/ with frontmatter (urls, raw_source)
     and body sections: ## Источник, ## Связь с inbox, ## Извлечённые концепты.
  2. Find concept notes whose titles or aliases appear in the raw note body
     (fuzzy substring match) and append `## Источники\n- [[Source]]` to them.

No LLM calls. Idempotent — safe to re-run.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Allow `python backfill_sources.py` from any cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Корень хранилища: BRAIN_ROOT, иначе родитель каталога скриптов (05_Scripts/..).
DEFAULT_ROOT = Path(os.environ.get("BRAIN_ROOT", Path(__file__).resolve().parent.parent))

import frontmatter

from sleep_cycle.dedup import index_wiki
from sleep_cycle.loader import extract_urls
from sleep_cycle.writer import add_source_backlink, create_source


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    raw_dir = args.root / "00_Raw"
    wiki_dir = args.root / "01_Wiki"

    wiki_entries = index_wiki(wiki_dir)
    # Map basename → (title, path) for seed/concept lookup
    concept_lookup: list[tuple[str, Path, list[str]]] = []
    for e in wiki_entries:
        # Skip sources themselves to avoid self-linking
        if e.path.parent.name == "sources":
            continue
        concept_lookup.append((e.title, e.path, e.aliases))

    created_sources = 0
    backlinks_added = 0
    skipped = 0

    for raw_path in sorted(raw_dir.rglob("*.md")):
        if raw_path.name.lower() == "readme.md":
            continue
        try:
            post = frontmatter.load(raw_path)
        except Exception:
            continue
        urls = extract_urls(post.content or "")
        if not urls:
            skipped += 1
            continue

        raw_title = post.metadata.get("title") or raw_path.stem
        raw_title = str(raw_title)
        body_lower = (post.content or "").lower()

        # Find concepts mentioned in this raw note.
        matched_concepts: list[tuple[str, Path]] = []
        for title, cpath, aliases in concept_lookup:
            terms = [title, *aliases]
            for term in terms:
                if not term or len(term) < 3:
                    continue
                if term.lower() in body_lower:
                    matched_concepts.append((title, cpath))
                    break

        concept_titles = [t for t, _ in matched_concepts]
        rel_raw = raw_path.relative_to(args.root)
        print(f"→ {rel_raw}: {len(urls)} URLs, {len(matched_concepts)} concept matches")

        if args.dry_run:
            for title, _ in matched_concepts[:5]:
                print(f"    would link: [[{title}]]")
            continue

        source_path = create_source(
            wiki_dir,
            raw_path=raw_path,
            raw_title=raw_title,
            urls=urls,
            concept_titles=concept_titles,
        )
        source_title = source_path.stem.replace("_", " ")
        created_sources += 1

        for _, cpath in matched_concepts:
            before = cpath.read_text(encoding="utf-8")
            add_source_backlink(cpath, source_title)
            after = cpath.read_text(encoding="utf-8")
            if after != before:
                backlinks_added += 1

    print(
        f"\n✓ Done. Sources processed: {created_sources}. "
        f"Backlinks added: {backlinks_added}. Raw notes without URLs: {skipped}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
