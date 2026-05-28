# sleep_cycle

Python+LLM реализация навыка [[vault-sleep-cycle]]. Читает заметки из `00_Raw/`, извлекает концепты через Claude, пишет атомарные страницы в `01_Wiki/`, обновляет `03_Meta/Master_Index.md` и логирует в `03_Meta/Log.md`.

## Установка

```bash
cd 05_Scripts/sleep_cycle
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # настрой LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_FALLBACK_MODEL
```

## Использование

```bash
# Dry-run — показать план без записи
python run.py --limit 5 --dry-run

# Реальный прогон на 5 файлах
python run.py --limit 5

# Архивировать обработанное (по умолчанию помечает status: consolidated)
python run.py --limit 5 --archive

# Запустить graphify update после успеха
python run.py --limit 5 --graphify
```

## Идемпотентность

- Дедуп по SHA-1 содержимого: уже обработанные файлы (`status: consolidated` во frontmatter) пропускаются.
- При совпадении нового концепта с существующей вики-страницей (по title или alias через fuzzy-match) — append вместо create.
