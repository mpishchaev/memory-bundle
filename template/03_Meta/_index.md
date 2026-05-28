# 03_Meta — Управление хранилищем, индексы и логи

Служебный слой: навигационные карты, журналы системы и шаблоны метаданных. Сам по себе не является памятью — это «диспетчерская» vault'а.

## Содержание

| Файл | Назначение |
|---|---|
| [`Master_Index.md`](Master_Index.md) | Навигационная точка входа по доменам (🧠 AI/Agents, 🗂️ Memory, 💻 Systems, 🧰 Tools). |
| [`hot.md`](hot.md) | Активные контексты и текущие приоритеты. |
| [`Log.md`](Log.md) | Журнал прогонов `vault-sleep-cycle`, `vault-maintenance`, `update_indexes.py`. Append-only. |
| [`Inbox_Concepts.md`](Inbox_Concepts.md) | Очередь свежеконсолидированных концептов, ожидающих ручной категоризации в `Master_Index`. |
| [`templates/`](templates/) | YAML-шаблоны заметок: `concept.md`, `project.md`, `task.md`, `daily.md`. |

## Правила

- `Log.md` и `Inbox_Concepts.md` пишутся скриптами `05_Scripts/` — не редактировать формат вручную.
- `Master_Index.md` и `hot.md` ведутся вручную (или агентом по запросу пользователя).
- Каталог не сканируется `vault-maintenance` на YAML — это мета-документы, не страницы графа.

## Связи

- [[01_Wiki]] — куда `Inbox_Concepts` направляет концепты на категоризацию.
- [[05_Scripts]] — скрипты, пишущие в `Log.md` и `Inbox_Concepts.md`.

<!-- INDEX:AUTO START — сгенерировано 05_Scripts/update_indexes.py, не редактировать вручную -->
<!-- INDEX:AUTO END -->
