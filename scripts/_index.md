# 05_Scripts — Автоматизация хранилища

Скрипты жизненного цикла vault'а: консолидация, проверка здоровья, обновление индексов.
Инфраструктурный слой (не память).

## Содержание

| Путь | Назначение |
|---|---|
| `sleep_cycle/` | Конвейер `00_Raw → 01_Wiki` (консолидация). `run.py` — оркестратор; `extractor.py`, `loader.py`, `writer.py`, `dedup.py` — этапы. |
| `maintenance/` | Здоровье vault'а: `check.py` (битые ссылки, сироты, YAML), `find_duplicates.py`, `merge_duplicates.py`. |
| `update_indexes.py` | Регенерация авто-секций всех `_index.md`. Чистый stdlib. |
| `backfill_sources.py` | Бэкфилл `01_Wiki/sources/` из URL'ов в raw-заметках. |
| `install_obsidian.sh` | Установка Obsidian Desktop + CLI. |
| `link_skills.sh` | Симлинки навыков `06_Skills/` в каталоги агентов. |

## Правила запуска

```bash
# Консолидация Raw → Wiki
cd 05_Scripts/sleep_cycle && .venv/bin/python run.py --limit 10

# Health-check (попутно освежает авто-секции _index.md)
.venv/bin/python ../maintenance/check.py --report

# Только обновить индексы
python 05_Scripts/update_indexes.py --root /home/ffazy/Projects/00__Brain
```

- `update_indexes.py` вызывается автоматически из `sleep_cycle/run.py` и `maintenance/check.py`.
- Скрипты, индексирующие концепты, пропускают `README.md` и `_index.md`.

## Связи

- [[vault-sleep-cycle]], [[vault-maintenance]] — навыки-обёртки над этими скриптами.
- [[Log]] — куда скрипты пишут результаты прогонов.
- [[AGENTS.md]] — общий протокол управления хранилищем.

<!-- INDEX:AUTO START — сгенерировано 05_Scripts/update_indexes.py, не редактировать вручную -->

_Обновлено: 2026-05-22 23:06_

| Подпапка | .md файлов |
|---|---|
| `maintenance/` | 0 |
| `sleep_cycle/` | 0 |

**Всего .md в каталоге:** 0
<!-- INDEX:AUTO END -->
