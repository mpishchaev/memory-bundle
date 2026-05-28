"""Find near-duplicate concepts in 01_Wiki/.

Compares title + aliases across all wiki pages pairwise using rapidfuzz
WRatio. Reports pairs above the similarity threshold so the user can
decide whether to merge.

Run:
    python find_duplicates.py             # threshold 85
    python find_duplicates.py --min 75    # broader sweep
    python find_duplicates.py --cross-category    # only inter-category pairs
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

import frontmatter
from rapidfuzz import fuzz


@dataclass
class Entry:
    path: Path
    title: str
    aliases: list[str]
    category: str

    @property
    def terms(self) -> list[str]:
        return [self.title, *self.aliases]


def load_entries(wiki_dir: Path) -> list[Entry]:
    out: list[Entry] = []
    for path in wiki_dir.rglob("*.md"):
        if path.name.lower() in ("readme.md", "_index.md"):
            continue
        # Skip sources: they're citation entities, not concepts.
        if path.parent.name == "sources":
            continue
        try:
            post = frontmatter.load(path)
        except Exception:
            continue
        title = str(post.metadata.get("title") or path.stem.replace("_", " "))
        aliases = post.metadata.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [aliases]
        out.append(
            Entry(
                path=path,
                title=title,
                aliases=[str(a) for a in aliases],
                category=path.parent.name,
            )
        )
    return out


def best_pair_score(a: Entry, b: Entry) -> tuple[int, str, str]:
    best = (0, a.title, b.title)
    for ta in a.terms:
        for tb in b.terms:
            score = int(fuzz.WRatio(ta, tb))
            if score > best[0]:
                best = (score, ta, tb)
    return best


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(os.environ.get("BRAIN_ROOT", Path(__file__).resolve().parent.parent.parent)))
    p.add_argument("--min", type=int, default=85, help="Similarity threshold 0-100")
    p.add_argument("--cross-category", action="store_true", help="Only show cross-category pairs")
    p.add_argument("--limit", type=int, default=80)
    args = p.parse_args()

    entries = load_entries(args.root / "01_Wiki")
    print(f"Loaded {len(entries)} concept entries.")

    pairs: list[tuple[int, Entry, Entry, str, str]] = []
    n = len(entries)
    for i in range(n):
        for j in range(i + 1, n):
            if args.cross_category and entries[i].category == entries[j].category:
                continue
            score, ta, tb = best_pair_score(entries[i], entries[j])
            if score >= args.min:
                pairs.append((score, entries[i], entries[j], ta, tb))

    pairs.sort(key=lambda x: -x[0])
    print(f"Pairs ≥ {args.min}: {len(pairs)}\n")
    for score, a, b, ta, tb in pairs[: args.limit]:
        ra = a.path.relative_to(args.root)
        rb = b.path.relative_to(args.root)
        ta_disp = f'"{ta}"' if ta != a.title else ""
        tb_disp = f'"{tb}"' if tb != b.title else ""
        print(f"  {score:3d}  {a.category:14s} {a.title} {ta_disp}")
        print(f"        {b.category:14s} {b.title} {tb_disp}")
        print(f"        {ra}")
        print(f"        {rb}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
