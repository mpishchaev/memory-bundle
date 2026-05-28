"""Two-pass concept extraction from a raw note via OpenAI-compatible LLM.

Pass 1 — discover atomic concept candidates (title, category, language).
Pass 2 — produce full Concept records with cross-links between siblings.

Supports any OpenAI-compatible endpoint with primary + fallback models.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from openai import OpenAI


CATEGORIES = ["concepts", "technology", "patterns", "people", "organizations", "sources"]

TAXONOMY_BLOCK = """## Таксономия 01_Wiki/

- `concepts/`     — абстрактные идеи, теории, фреймворки, методологии (PARA Method, Knowledge Graph, Boring AI, Cognitive Architecture)
- `technology/`   — конкретные инструменты, API, фреймворки, языки, протоколы (Claude API, LangChain, Obsidian, Webhooks, n8n)
- `patterns/`     — прикладные паттерны, техники, рецепты, workflow'ы (Speed to Lead, RAG, ETL, Lead Follow-up Automation)
- `people/`       — персоны, авторы, инфлюенсеры (Tiago Forte, Andrej Karpathy)
- `organizations/`— компании, продукты, проекты, сообщества (Anthropic, OpenAI, Notion)
- `sources/`      — исходные материалы (видео, статьи, треды, книги) — НЕ создавай этот тип в Pass 1, источники готовятся отдельным пайплайном

Правила:
- concepts vs patterns: концепт — «что это / зачем»; паттерн — «как делать».
- concepts vs technology: концепт абстрактен; технология — конкретный инструмент с вендором.
- НЕ создавай категорию `sources` — её заполняет отдельный механизм. Если raw-заметка — это конспект видео/статьи, всё равно извлекай из неё атомарные концепты, а сама ссылка-источник попадёт в backlink автоматически.
- Если не уверен — `concepts` (дефолт).
"""


@dataclass
class ConceptCandidate:
    title: str
    category: str = "concepts"
    language: str = "ru"


@dataclass
class Concept:
    title: str
    category: str = "concepts"
    aliases: list[str] = field(default_factory=list)
    summary: str = ""
    body: str = ""
    tags: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)


# ---------- prompts ----------

PASS1_SYSTEM = """Ты — компонент когнитивной системы Unified Brain (PARA + Obsidian).
Задача Pass 1: из сырой заметки выделить АТОМАРНЫЕ концепты-кандидаты.

{taxonomy}

Критерий атомарности:
- Один концепт = один термин, который можно объяснить без ссылки на исходную статью.
- НЕ концепты: заголовки-зонтики («Подходы к X», «5 типов Y»), названия статей.
- 3–7 концептов на заметку.

Канонический язык title:
- EN, если термин общеупотребим на английском (Speed to Lead, RAG, Webhook).
- RU, если русский эквивалент устойчив и не имеет короткого английского аналога.
- Если оба распространены — выбирай язык оригинального источника.

Существующие концепты в вики (НЕ дублируй):
{wiki_index}

Отвечай СТРОГО JSON-массивом, никакого текста до/после:
[
  {{"title": "...", "category": "concepts|technology|patterns|people|organizations", "language": "ru|en"}}
]
"""

PASS2_SYSTEM = """Ты — компонент когнитивной системы Unified Brain (PARA + Obsidian).
Задача Pass 2: написать детальное описание каждого концепта из батча с обязательной cross-линковкой между соседями.

{taxonomy}

Жёсткие правила для поля `related`:
1. Перечисляй сначала концепты из ТОГО ЖЕ батча (соседей по этой raw-заметке), если они семантически связаны. Это обязательно для ≥50% концептов батча.
2. Затем — существующие концепты вики (см. индекс ниже), если связь ПРЯМАЯ. Не вставляй [[Knowledge Graph]] или другие seed-узлы для красоты — только если концепт действительно касается графов знаний / методологий памяти.
3. Если осмысленных связей нет — оставь массив пустым.

Структура `body` (markdown, 100–250 слов):
- Начни с подзаголовка `## Контекст` (только если содержание шире `summary`).
- Подзаголовки `## Связи` ВНУТРИ body НЕ пиши — связи выводятся отдельно из поля `related`.
- Без дублирования `title`/`summary`.

Существующие концепты вики:
{wiki_index}

Концепты-соседи этого батча:
{batch_titles}

Отвечай СТРОГО JSON-массивом в порядке батча:
[
  {{
    "title": "...",
    "category": "...",
    "aliases": ["синоним1"],
    "summary": "1-2 предложения сути",
    "body": "markdown-тело",
    "tags": ["wiki/concept", "domain/xxx"],
    "related": ["Сосед", "Существующий Концепт"]
  }}
]
"""


# ---------- helpers ----------

def _strip_to_json(text: str) -> str:
    fence = re.search(r"```(?:json)?\s*(\[.*\])\s*```", text, re.DOTALL)
    if fence:
        return fence.group(1)
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text.strip()


def _build_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ.get("LLM_BASE_URL"),
        api_key=os.environ.get("LLM_API_KEY", "sk-noop"),
    )


def _call_model(client: OpenAI, model: str, system: str, user: str) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        max_tokens=4096,
    )
    return resp.choices[0].message.content or ""


def _call_with_fallback(client: OpenAI, system: str, user: str) -> list[dict]:
    primary = os.environ.get("LLM_MODEL", "gemma4")
    fallback = os.environ.get("LLM_FALLBACK_MODEL")
    last_error: Exception | None = None
    for model in [m for m in (primary, fallback) if m]:
        try:
            raw = _call_model(client, model, system, user)
            return json.loads(_strip_to_json(raw))
        except Exception as exc:
            last_error = exc
            print(f"    ! model {model} failed: {exc}")
            continue
    raise RuntimeError(f"All models failed. Last error: {last_error}")


# ---------- public API ----------

def _wiki_index_str(wiki_titles_by_cat: dict[str, list[str]]) -> str:
    if not any(wiki_titles_by_cat.values()):
        return "(индекс пуст)"
    lines = []
    for cat in CATEGORIES:
        titles = wiki_titles_by_cat.get(cat, [])
        if titles:
            lines.append(f"- {cat}: " + ", ".join(titles[:50]))
    return "\n".join(lines)


def discover_concepts(
    *,
    raw_title: str,
    raw_body: str,
    wiki_titles_by_cat: dict[str, list[str]],
    client: OpenAI,
) -> list[ConceptCandidate]:
    system = PASS1_SYSTEM.format(
        taxonomy=TAXONOMY_BLOCK,
        wiki_index=_wiki_index_str(wiki_titles_by_cat),
    )
    user = f"# Сырая заметка: {raw_title}\n\n{raw_body[:12000]}"
    items = _call_with_fallback(client, system, user)
    out: list[ConceptCandidate] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("title"):
            continue
        cat = item.get("category", "concepts")
        if cat not in CATEGORIES or cat == "sources":
            cat = "concepts"
        out.append(
            ConceptCandidate(
                title=str(item["title"]).strip(),
                category=cat,
                language=item.get("language", "ru"),
            )
        )
    return out


def detail_concepts(
    *,
    raw_title: str,
    raw_body: str,
    candidates: list[ConceptCandidate],
    wiki_titles_by_cat: dict[str, list[str]],
    client: OpenAI,
) -> list[Concept]:
    if not candidates:
        return []
    batch_titles = "\n".join(f"- {c.title} ({c.category})" for c in candidates)
    system = PASS2_SYSTEM.format(
        taxonomy=TAXONOMY_BLOCK,
        wiki_index=_wiki_index_str(wiki_titles_by_cat),
        batch_titles=batch_titles,
    )
    user = (
        f"# Сырая заметка: {raw_title}\n\n{raw_body[:12000]}\n\n"
        f"# Концепты этого батча (Pass 1):\n{batch_titles}\n"
        "Напиши JSON-массив детальных концептов В ТОМ ЖЕ ПОРЯДКЕ."
    )
    items = _call_with_fallback(client, system, user)
    cand_by_title = {c.title: c for c in candidates}
    out: list[Concept] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("title"):
            continue
        title = str(item["title"]).strip()
        cand = cand_by_title.get(title)
        cat = item.get("category") or (cand.category if cand else "concepts")
        if cat not in CATEGORIES:
            cat = "concepts"
        out.append(
            Concept(
                title=title,
                category=cat,
                aliases=[str(a) for a in (item.get("aliases") or [])],
                summary=str(item.get("summary", "")).strip(),
                body=str(item.get("body", "")).strip(),
                tags=item.get("tags") or ["wiki/concept"],
                related=[str(r) for r in (item.get("related") or [])],
            )
        )
    return out


def extract_concepts(
    *,
    raw_title: str,
    raw_body: str,
    wiki_titles_by_cat: dict[str, list[str]],
    brain_root: Path,  # kept for API compatibility; unused in v2
    client: OpenAI | None = None,
) -> list[Concept]:
    client = client or _build_client()
    candidates = discover_concepts(
        raw_title=raw_title,
        raw_body=raw_body,
        wiki_titles_by_cat=wiki_titles_by_cat,
        client=client,
    )
    print(f"    pass1: {len(candidates)} candidates → " + ", ".join(f"{c.title}[{c.category}]" for c in candidates))
    return detail_concepts(
        raw_title=raw_title,
        raw_body=raw_body,
        candidates=candidates,
        wiki_titles_by_cat=wiki_titles_by_cat,
        client=client,
    )
