"""Find existing Wiki pages matching a new concept by title or alias."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import frontmatter
from rapidfuzz import fuzz, process


@dataclass
class WikiEntry:
    path: Path
    title: str
    aliases: list[str]

    @property
    def search_terms(self) -> list[str]:
        return [self.title, *self.aliases]


def index_wiki(wiki_dir: Path) -> list[WikiEntry]:
    entries: list[WikiEntry] = []
    for path in wiki_dir.rglob("*.md"):
        if path.name.lower() in ("readme.md", "_index.md"):
            continue
        try:
            post = frontmatter.load(path)
        except Exception:
            continue
        title = post.metadata.get("title") or path.stem.replace("_", " ")
        aliases = post.metadata.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [aliases]
        entries.append(WikiEntry(path=path, title=str(title), aliases=[str(a) for a in aliases]))
    return entries


def find_match(concept_name: str, entries: list[WikiEntry], threshold: int = 88) -> WikiEntry | None:
    if not entries:
        return None
    pool: list[tuple[str, WikiEntry]] = []
    for entry in entries:
        for term in entry.search_terms:
            pool.append((term, entry))
    choices = [term for term, _ in pool]
    result = process.extractOne(concept_name, choices, scorer=fuzz.WRatio)
    if not result:
        return None
    matched, score, idx = result
    if score < threshold:
        return None
    return pool[idx][1]
