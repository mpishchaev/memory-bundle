"""Write atomic concept notes into 01_Wiki/<category>/, append to existing,
update Log + Inbox_Concepts. Trusts LLM-generated body verbatim."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import frontmatter

from .extractor import CATEGORIES, Concept


def _slugify(title: str) -> str:
    safe = "".join(c if c.isalnum() or c in (" ", "-", "_") else "" for c in title)
    return safe.strip().replace(" ", "_") or "Concept"


def _today() -> str:
    return dt.date.today().isoformat()


def _now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def _category_dir(wiki_dir: Path, category: str) -> Path:
    cat = category if category in CATEGORIES else "concepts"
    d = wiki_dir / cat
    d.mkdir(parents=True, exist_ok=True)
    return d


def _format_links_block(related: list[str], body: str) -> str:
    if not related:
        return ""
    if "## Связи" in body:
        return "\n\n" + "\n".join(f"- [[{r}]]" for r in related) + "\n"
    return "\n\n## Связи\n\n" + "\n".join(f"- [[{r}]]" for r in related) + "\n"


def create_concept(wiki_dir: Path, concept: Concept) -> Path:
    target_dir = _category_dir(wiki_dir, concept.category)
    path = target_dir / f"{_slugify(concept.title)}.md"
    if path.exists():
        return append_concept(path, concept)

    today = _today()
    body = concept.body.strip()
    content = f"# {concept.title}\n\n## Определение\n\n{concept.summary}\n"
    if body:
        content += f"\n{body}\n"
    content += _format_links_block(concept.related, body)

    post = frontmatter.Post(
        content=content,
        **{
            "title": concept.title,
            "aliases": concept.aliases,
            "tags": concept.tags,
            "category": concept.category,
            "created": today,
            "updated": today,
            "status": "consolidated",
        },
    )
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    return path


def append_concept(existing_path: Path, concept: Concept) -> Path:
    post = frontmatter.load(existing_path)
    post.metadata["updated"] = _today()
    aliases = set(post.metadata.get("aliases") or [])
    aliases.update(concept.aliases)
    post.metadata["aliases"] = sorted(aliases)

    body = concept.body.strip()
    block = f"\n\n---\n### Дополнено {_today()}\n\n{concept.summary}\n"
    if body:
        block += f"\n{body}\n"
    block += _format_links_block(concept.related, body)
    post.content = (post.content or "").rstrip() + block
    existing_path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    return existing_path


def mark_raw_consolidated(raw_path: Path, archive_dir: Path | None = None) -> Path:
    post = frontmatter.load(raw_path)
    post.metadata["status"] = "consolidated"
    post.metadata["updated"] = _today()
    raw_path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    if archive_dir is not None:
        archive_dir.mkdir(parents=True, exist_ok=True)
        target = archive_dir / raw_path.name
        raw_path.rename(target)
        return target
    return raw_path


def append_log(log_path: Path, message: str) -> None:
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f"- **{_now()}** — {message}\n")


def _domain_kind(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "video"
    if "github.com" in url or "gitlab.com" in url:
        return "repo"
    if "twitter.com" in url or "x.com" in url:
        return "thread"
    return "web"


def create_source(
    wiki_dir: Path,
    *,
    raw_path: Path,
    raw_title: str,
    urls: list[str],
    concept_titles: list[str],
) -> Path:
    """Create or update 01_Wiki/sources/<slug>.md for a raw note with URLs."""
    sources_dir = wiki_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify(raw_title)[:80]
    path = sources_dir / f"{slug}.md"

    today = _today()
    kinds = sorted({_domain_kind(u) for u in urls}) or ["web"]
    primary_kind = kinds[0]

    if path.exists():
        post = frontmatter.load(path)
        existing_urls = set(post.metadata.get("urls") or [])
        existing_urls.update(urls)
        post.metadata["urls"] = sorted(existing_urls)
        post.metadata["updated"] = today
        existing_concepts = set()
        for line in (post.content or "").splitlines():
            line = line.strip()
            if line.startswith("- [[") and line.endswith("]]"):
                existing_concepts.add(line[4:-2])
        new_concepts = [t for t in concept_titles if t not in existing_concepts]
        if new_concepts:
            block = "\n" + "\n".join(f"- [[{t}]]" for t in new_concepts) + "\n"
            if "## Извлечённые концепты" in post.content:
                post.content = post.content.rstrip() + block
            else:
                post.content = (post.content or "").rstrip() + "\n\n## Извлечённые концепты\n" + block
        path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
        return path

    url_block = "\n".join(f"- {u}" for u in urls) or "_(нет URL)_"
    concepts_block = "\n".join(f"- [[{t}]]" for t in concept_titles) or "_(пока пусто)_"
    content = (
        f"# {raw_title}\n\n"
        f"## Источник\n\n{url_block}\n\n"
        f"## Связь с inbox\n\n- [[{raw_path.stem}]]\n\n"
        f"## Извлечённые концепты\n\n{concepts_block}\n"
    )
    post = frontmatter.Post(
        content=content,
        **{
            "title": raw_title,
            "aliases": [],
            "tags": ["wiki/source", f"source/{primary_kind}"],
            "category": "sources",
            "urls": urls,
            "raw_source": str(raw_path.relative_to(wiki_dir.parent)) if raw_path.is_absolute() else str(raw_path),
            "created": today,
            "updated": today,
            "status": "consolidated",
        },
    )
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    return path


def add_source_backlink(concept_path: Path, source_title: str) -> None:
    """Append [[Source]] under ## Источники in a concept note (idempotent)."""
    post = frontmatter.load(concept_path)
    content = post.content or ""
    marker = f"[[{source_title}]]"
    if marker in content:
        return
    if "## Источники" in content:
        post.content = content.rstrip() + f"\n- {marker}\n"
    else:
        post.content = content.rstrip() + f"\n\n## Источники\n\n- {marker}\n"
    post.metadata["updated"] = _today()
    concept_path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")


def append_inbox(inbox_path: Path, items: list[tuple[str, str]]) -> None:
    """items: list of (title, category)."""
    if not items:
        return
    if not inbox_path.exists():
        inbox_path.write_text(
            "# Inbox: Свежеконсолидированные концепты\n\n"
            "Ожидают ручной категоризации в [[Master_Index]]. Группировка по типу сущности.\n\n"
            + "\n".join(f"## {c}\n" for c in CATEGORIES),
            encoding="utf-8",
        )

    text = inbox_path.read_text(encoding="utf-8")
    grouped: dict[str, list[str]] = {c: [] for c in CATEGORIES}
    for title, cat in items:
        grouped.setdefault(cat if cat in CATEGORIES else "concepts", []).append(title)

    for cat, titles in grouped.items():
        if not titles:
            continue
        header = f"## {cat}"
        if header in text:
            entries = "\n".join(f"- [[{t}]]" for t in titles) + "\n"
            text = text.replace(header + "\n", header + "\n" + entries, 1)
        else:
            text += f"\n{header}\n" + "\n".join(f"- [[{t}]]" for t in titles) + "\n"

    inbox_path.write_text(text, encoding="utf-8")
