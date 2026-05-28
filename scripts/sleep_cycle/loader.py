"""Read raw notes from 00_Raw/, normalize, filter already-consolidated."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter

URL_RE = re.compile(r"https?://[^\s)\]\}>'\"]+")


def extract_urls(text: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in URL_RE.findall(text):
        url = raw.rstrip(".,;:!?")
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


@dataclass
class RawNote:
    path: Path
    title: str
    body: str
    sha1: str
    metadata: dict
    urls: list[str] = field(default_factory=list)

    @property
    def is_consolidated(self) -> bool:
        return self.metadata.get("status") == "consolidated"


def _sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def load_raw_notes(raw_dir: Path, limit: int | None = None) -> list[RawNote]:
    notes: list[RawNote] = []
    for path in sorted(raw_dir.rglob("*.md")):
        if path.name.lower() in ("readme.md", "_index.md"):
            continue
        try:
            post = frontmatter.load(path)
        except Exception:
            text = path.read_text(encoding="utf-8", errors="replace")
            post = frontmatter.Post(text, **{})
        body = post.content.strip()
        if not body:
            continue
        title = post.metadata.get("title") or path.stem.replace("_", " ")
        note = RawNote(
            path=path,
            title=str(title),
            body=body,
            sha1=_sha1(body),
            metadata=dict(post.metadata),
            urls=extract_urls(body),
        )
        if note.is_consolidated:
            continue
        notes.append(note)
        if limit and len(notes) >= limit:
            break

    return notes
