#!/usr/bin/env bash
# =================================================================
#        Agent Memory Bundle - Unified Setup & Connection Script
# =================================================================
set -e

# Resolve the directory of the memory-bundle repository
BUNDLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default settings
VAULT_NAME=".brain"
CENTRAL_VAULT=""
PROJECT_ROOT="$(pwd)"

usage() {
    echo "Использование: $0 [опции]"
    echo ""
    echo "Опции:"
    echo "  -d, --dir <name>      Имя каталога для локальной памяти (по умолчанию: .brain)"
    echo "  -c, --central <path>  Подключить существующую центральную память по указанному пути"
    echo "  -h, --help            Показать справку"
    echo ""
    echo "Примеры:"
    echo "  $0                  # Инициализировать локальную память .brain/"
    echo "  $0 -d brain         # Инициализировать локальную память в папке brain/"
    echo "  $0 -c ~/Brain       # Подключить центральную память"
    exit 0
}

# Parse options
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -d|--dir) VAULT_NAME="$2"; shift ;;
        -c|--central) CENTRAL_VAULT="$2"; shift ;;
        -h|--help) usage ;;
        *) echo "Неизвестный параметр: $1"; usage ;;
    esac
    shift
done

VAULT_DIR="$PROJECT_ROOT/$VAULT_NAME"

echo "================================================================="
echo "⚙️  Инициализация агентской памяти в проекте: $PROJECT_ROOT"
echo "================================================================="

# 1. Setup Vault Directory Structure
if [ -n "$CENTRAL_VAULT" ]; then
    # Central Vault Mode
    CENTRAL_PATH="$(realpath "$CENTRAL_VAULT")"
    if [ ! -d "$CENTRAL_PATH" ]; then
        echo "❌ Ошибка: Директория центральной памяти '$CENTRAL_PATH' не существует."
        exit 1
    fi
    echo "🔗 Режим центральной памяти. Создание ссылки на '$CENTRAL_PATH'..."
    if [ -L "$VAULT_DIR" ]; then
        rm "$VAULT_DIR"
    elif [ -e "$VAULT_DIR" ]; then
        echo "⚠️  Внимание: Найден существующий файл/папка '$VAULT_NAME'. Создаем резервную копию..."
        mv "$VAULT_DIR" "${VAULT_DIR}.bak_$(date +%s)"
    fi
    ln -s "$CENTRAL_PATH" "$VAULT_DIR"
    echo "✅ Символическая ссылка создана: $VAULT_NAME -> $CENTRAL_PATH"
else
    # Local Vault Mode
    echo "📁 Режим локальной памяти. Инициализация папки '$VAULT_NAME'..."
    if [ -d "$VAULT_DIR" ]; then
        echo "ℹ️  Папка '$VAULT_NAME' уже существует в проекте. Обновляем скрипты и навыки..."
    else
        mkdir -p "$VAULT_DIR"
    fi

    # Copy template folders
    for dir in 00_Raw 01_Wiki 02_Memory 03_Meta 04_Archive; do
        if [ ! -d "$VAULT_DIR/$dir" ]; then
            echo "   Создание $VAULT_NAME/$dir..."
            cp -r "$BUNDLE_DIR/template/$dir" "$VAULT_DIR/"
        fi
    done

    # Ensure subcategories of 01_Wiki exist
    for sub in concepts technology patterns people organizations sources; do
        mkdir -p "$VAULT_DIR/01_Wiki/$sub"
    done

    # Ensure templates directory exists
    mkdir -p "$VAULT_DIR/03_Meta/templates"

    # Copy .obsidian configurations if not existing
    if [ ! -d "$VAULT_DIR/.obsidian" ]; then
        cp -r "$BUNDLE_DIR/template/.obsidian" "$VAULT_DIR/"
    fi

    # Copy automation scripts (05_Scripts)
    echo "📂 Обновление автоматизационных скриптов в $VAULT_NAME/05_Scripts/..."
    mkdir -p "$VAULT_DIR/05_Scripts"
    cp -r "$BUNDLE_DIR/scripts/"* "$VAULT_DIR/05_Scripts/"

    # Copy Agent Skills (06_Skills)
    echo "📂 Обновление навыков агентов в $VAULT_NAME/06_Skills/..."
    mkdir -p "$VAULT_DIR/06_Skills"
    cp -r "$BUNDLE_DIR/skills/"* "$VAULT_DIR/06_Skills/"
    
    # Create default .env in the vault for LLM API config if not exists
    if [ ! -f "$VAULT_DIR/05_Scripts/sleep_cycle/.env" ]; then
        echo "   Создание файла конфигурации .env..."
        if [ -f "$VAULT_DIR/05_Scripts/sleep_cycle/.env.example" ]; then
            cp "$VAULT_DIR/05_Scripts/sleep_cycle/.env.example" "$VAULT_DIR/05_Scripts/sleep_cycle/.env"
        else
            cat <<EOF > "$VAULT_DIR/05_Scripts/sleep_cycle/.env"
# Конфигурация OpenAI-совместимого API для Sleep Cycle
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o
LLM_FALLBACK_MODEL=gpt-4o-mini
BRAIN_ROOT=$VAULT_DIR

# Ключ API Google Gemini для семантического обогащения графа знаний в Graphify
GEMINI_API_KEY=AIzaSy...
GOOGLE_API_KEY=AIzaSy...
EOF
        fi
    fi
    
    echo "✅ Инициализация структуры папок завершена."
fi

# 2. Setup Python Virtual Environment (Local mode only)
if [ -z "$CENTRAL_VAULT" ]; then
    echo "🐍 Настройка Python-окружения..."
    VENV_DIR="$VAULT_DIR/.venv"
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
    fi
    
    # Install dependencies
    echo "   Установка зависимостей Python..."
    "$VENV_DIR/bin/pip" install --upgrade pip --quiet
    "$VENV_DIR/bin/pip" install openai python-frontmatter rapidfuzz python-dotenv --quiet
    echo "✅ Зависимости Python установлены."
fi

# 3. Setup Graphify
echo "📊 Настройка Graphify..."
if ! command -v graphify &> /dev/null; then
    # Note: The PyPI package is registered as 'graphifyy' (with two 'y's) while the CLI command is 'graphify' (one 'y').
    echo "   Инструмент 'graphify' не найден. Попытка установки через uv..."
    if command -v uv &> /dev/null; then
        uv tool install graphifyy
    else
        echo "   'uv' не найден. Установка через pip..."
        pip3 install --user graphifyy --quiet
    fi
fi

if command -v graphify &> /dev/null; then
    echo "✅ Graphify успешно установлен/обнаружен."
    
    # Setup .graphifyignore
    if [ ! -f "$PROJECT_ROOT/.graphifyignore" ]; then
        if [ -f "$BUNDLE_DIR/template/.graphifyignore" ]; then
            cp "$BUNDLE_DIR/template/.graphifyignore" "$PROJECT_ROOT/"
            echo "   Создан файл .graphifyignore в корне проекта."
        else
            printf "graphify-out/\n.graphifyignore\n" > "$PROJECT_ROOT/.graphifyignore"
            echo "   Создан файл .graphifyignore по умолчанию."
        fi
    fi
    
    # Run graphify install to sync skill versions and hooks globally
    graphify install 2>/dev/null || true
    
    # Run graphify update to build initial graph
    echo "   Генерация начального графа знаний проекта..."
    graphify update "$PROJECT_ROOT" || echo "⚠️ Предупреждение: Не удалось запустить graphify update. Проверьте ваш проект."
    
    # Add to .gitignore if exists
    if [ -f "$PROJECT_ROOT/.gitignore" ]; then
        if ! grep -q "graphify-out/" "$PROJECT_ROOT/.gitignore"; then
            echo -e "\n# Graphify outputs\ngraphify-out/\n.graphifyignore" >> "$PROJECT_ROOT/.gitignore"
            echo "   Добавлен graphify-out/ в .gitignore."
        fi
        if ! grep -q "$VAULT_NAME/" "$PROJECT_ROOT/.gitignore" && [ "$VAULT_NAME" = ".brain" ]; then
            echo -e "\n# Local agent memory vault\n.brain/\n" >> "$PROJECT_ROOT/.gitignore"
            echo "   Добавлен $VAULT_NAME/ в .gitignore."
        fi
    fi
else
    echo "⚠️ Предупреждение: Утилиту graphify не удалось установить. Пропустите этот шаг."
fi

# 4. Symlink Agent Skills to Active Harnesses
echo "🔗 Подключение навыков к средам выполнения ИИ..."

link_skill() {
    local source_skill="$1"
    local target_dir="$2"
    local name="$(basename "$source_skill")"
    mkdir -p "$target_dir"
    
    if [ -e "$target_dir/$name" ] || [ -L "$target_dir/$name" ]; then
        rm -rf "$target_dir/$name"
    fi
    ln -s "$source_skill" "$target_dir/$name"
    echo "   ✅ Навык $name прилинкован к $target_dir"
}

# Source skills folder path
SKILLS_SRC_DIR="$VAULT_DIR/06_Skills"

# Helper for automatic harness linking
link_all_skills() {
    local target_skills_dir="$1"
    # Find all skills under 06_Skills
    for skill_path in "$SKILLS_SRC_DIR"/*; do
        if [ -d "$skill_path" ]; then
            link_skill "$skill_path" "$target_skills_dir"
        fi
    done
}

# Normalize instructions file casing to avoid duplicate files on case-sensitive Linux FS
if [ ! -f "$PROJECT_ROOT/AGENTS.md" ]; then
    if [ -f "$PROJECT_ROOT/Agents.md" ]; then
        mv "$PROJECT_ROOT/Agents.md" "$PROJECT_ROOT/AGENTS.md"
        echo "   Нормализовано имя файла: Agents.md -> AGENTS.md"
    elif [ -f "$PROJECT_ROOT/agents.md" ]; then
        mv "$PROJECT_ROOT/agents.md" "$PROJECT_ROOT/AGENTS.md"
        echo "   Нормализовано имя файла: agents.md -> AGENTS.md"
    fi
fi

# 4.1. Claude Code (.claude/skills/)
# Detect Claude Code if .claude folder exists, or any case variant of CLAUDE.md exists
if [ -d "$PROJECT_ROOT/.claude" ] || [ -f "$PROJECT_ROOT/CLAUDE.md" ] || [ -f "$PROJECT_ROOT/Claude.md" ] || [ -f "$PROJECT_ROOT/claude.md" ]; then
    echo "👉 Обнаружена среда Claude Code. Подключение навыков..."
    link_all_skills "$PROJECT_ROOT/.claude/skills"
    
    if command -v graphify &> /dev/null; then
        if [ -f "$PROJECT_ROOT/AGENTS.md" ]; then
            # Run graphify claude install to register hooks in .claude/settings.json
            graphify claude install || true
            
            # If CLAUDE.md was created with graphify section, move those rules to AGENTS.md
            if [ -f "$PROJECT_ROOT/CLAUDE.md" ]; then
                if ! grep -q "## graphify" "$PROJECT_ROOT/AGENTS.md"; then
                    echo "" >> "$PROJECT_ROOT/AGENTS.md"
                    cat "$PROJECT_ROOT/CLAUDE.md" >> "$PROJECT_ROOT/AGENTS.md"
                    echo "   Раздел graphify перенесен в AGENTS.md"
                fi
            fi
            
            # Setup CLAUDE.md as a clean redirect to AGENTS.md to avoid duplicate files/content
            echo "@AGENTS.md" > "$PROJECT_ROOT/CLAUDE.md"
            echo "   Файл CLAUDE.md настроен как перенаправление на AGENTS.md"
            rm -f "$PROJECT_ROOT/Claude.md" "$PROJECT_ROOT/claude.md"
        else
            # No AGENTS.md exists, so normalize case to CLAUDE.md if needed
            if [ ! -f "$PROJECT_ROOT/CLAUDE.md" ]; then
                if [ -f "$PROJECT_ROOT/Claude.md" ]; then
                    mv "$PROJECT_ROOT/Claude.md" "$PROJECT_ROOT/CLAUDE.md"
                elif [ -f "$PROJECT_ROOT/claude.md" ]; then
                    mv "$PROJECT_ROOT/claude.md" "$PROJECT_ROOT/CLAUDE.md"
                fi
            fi
            graphify claude install || true
        fi
    else
        # Graphify is not present but Claude Code environment is detected
        if [ -f "$PROJECT_ROOT/AGENTS.md" ]; then
            echo "@AGENTS.md" > "$PROJECT_ROOT/CLAUDE.md"
            rm -f "$PROJECT_ROOT/Claude.md" "$PROJECT_ROOT/claude.md"
        else
            if [ ! -f "$PROJECT_ROOT/CLAUDE.md" ]; then
                if [ -f "$PROJECT_ROOT/Claude.md" ]; then
                    mv "$PROJECT_ROOT/Claude.md" "$PROJECT_ROOT/CLAUDE.md"
                elif [ -f "$PROJECT_ROOT/claude.md" ]; then
                    mv "$PROJECT_ROOT/claude.md" "$PROJECT_ROOT/CLAUDE.md"
                fi
            fi
        fi
    fi
fi

# 4.2. Antigravity (.agents/rules, .agents/workflows)
if [ -d "$PROJECT_ROOT/.agents" ]; then
    echo "👉 Обнаружена среда Google Antigravity. Подключение навыков..."
    # Antigravity uses standard skills format, linked directly or via .agents/rules
    mkdir -p "$PROJECT_ROOT/.agents/skills"
    link_all_skills "$PROJECT_ROOT/.agents/skills"
    if command -v graphify &> /dev/null; then
        graphify antigravity install || true
    fi
fi

# 4.3. Codex (~/.codex/skills/)
if [ -d "$HOME/.codex" ]; then
    echo "👉 Обнаружена среда Codex. Подключение навыков..."
    link_all_skills "$HOME/.codex/skills"
    if command -v graphify &> /dev/null && [ -d "$PROJECT_ROOT/.codex" ]; then
        graphify codex install || true
    fi
fi

# 4.4. Hermes / OpenCode / OpenClaw (~/.opencode/skills/)
if [ -d "$HOME/.opencode" ]; then
    echo "👉 Обнаружена среда OpenCode. Подключение навыков..."
    # Clones/links into a subfolder for discovery
    mkdir -p "$HOME/.opencode/skills/memory-bundle"
    for skill_path in "$SKILLS_SRC_DIR"/*; do
        if [ -d "$skill_path" ]; then
            link_skill "$skill_path" "$HOME/.opencode/skills/memory-bundle"
        fi
    done
    if command -v graphify &> /dev/null && [ -d "$PROJECT_ROOT/.opencode" ]; then
        graphify opencode install || true
    fi
fi

# 4.5. Fallback - always link in the project root's local agent folder if none of the above are found
if [ ! -d "$PROJECT_ROOT/.claude" ] && [ ! -d "$PROJECT_ROOT/.agents" ]; then
    echo "ℹ️  Создание локального каталога навыков агента по умолчанию .claude/skills/..."
    link_all_skills "$PROJECT_ROOT/.claude/skills"
fi

# 5. Create Unified brain CLI Wrapper in the Project Root
echo "🛠️  Создание исполняемого CLI-файла 'brain'..."
CLI_FILE="$PROJECT_ROOT/brain"

# Resolve absolute path for script executions inside brain CLI
ABS_VAULT_DIR="$(realpath "$VAULT_DIR")"

cat <<EOF > "$CLI_FILE"
#!/usr/bin/env bash
# =================================================================
#        CLI утилита управления агентской памятью
# =================================================================
set -e

VAULT_PATH="$ABS_VAULT_DIR"
VENV_PYTHON="\$VAULT_PATH/.venv/bin/python3"

# Если виртуального окружения нет (например, в central-mode), используем системный python
if [ ! -f "\$VENV_PYTHON" ]; then
    VENV_PYTHON="python3"
fi

usage() {
    echo "Использование: ./brain [команда] [опции]"
    echo ""
    echo "Доступные команды:"
    echo "  sleep [--limit N] [--archive] [--graphify] [--dry-run]"
    echo "                        Запуск цикла сна (консолидация Raw в Wiki)"
    echo "  check [--report]      Проверка целостности графа памяти (maintenance)"
    echo "  duplicates [--min N]  Поиск похожих концептов (по умолчанию порог 85)"
    echo "  merge --winner <W> --loser <L> [--dry-run]"
    echo "                        Слияние двух дублирующихся заметок"
    echo "  index                 Пересчитать индексы _index.md во всех каталогах"
    echo "  graphify              Обновить граф связей codebase (graphify update)"
    echo "  help                  Показать это сообщение"
    exit 0
}

if [ -z "\$1" ]; then
    usage
fi

CMD="\$1"
shift

export BRAIN_ROOT="\$VAULT_PATH"

case "\$CMD" in
    sleep)
        "\$VENV_PYTHON" "\$VAULT_PATH/05_Scripts/sleep_cycle/run.py" "\$@"
        ;;
    check)
        "\$VENV_PYTHON" "\$VAULT_PATH/05_Scripts/maintenance/check.py" "\$@"
        ;;
    duplicates)
        "\$VENV_PYTHON" "\$VAULT_PATH/05_Scripts/maintenance/find_duplicates.py" "\$@"
        ;;
    merge)
        "\$VENV_PYTHON" "\$VAULT_PATH/05_Scripts/maintenance/merge_duplicates.py" "\$@"
        ;;
    index)
        "\$VENV_PYTHON" "\$VAULT_PATH/05_Scripts/update_indexes.py" "\$@"
        ;;
    graphify)
        if command -v graphify &> /dev/null; then
            graphify update "$PROJECT_ROOT"
        else
            echo "❌ Ошибка: Утилита graphify не найдена. Пожалуйста, установите её."
            exit 1
        fi
        ;;
    help|-h|--help)
        usage
        ;;
    *)
        echo "❌ Неизвестная команда: \$CMD"
        usage
        ;;
esac
EOF

chmod +x "$CLI_FILE"
echo "✅ CLI-файл 'brain' успешно создан в корне проекта: ./brain"

# 6. Configure Obsidian Ignores in Project Root
# If the user opens the project root as an Obsidian Vault, we must ensure graphify-out/
# and other build artifacts are ignored so they don't pollute the graph view.
echo "⚙️  Настройка игнорирования в Obsidian для корня проекта..."
mkdir -p "$PROJECT_ROOT/.obsidian"
TEMPLATE_APP_JSON="$BUNDLE_DIR/template/.obsidian/app.json"
PROJECT_APP_JSON="$PROJECT_ROOT/.obsidian/app.json"

python3 -c '
import json, os, sys
project_json = sys.argv[1]
template_json = sys.argv[2]
try:
    with open(template_json, "r") as f:
        t_data = json.load(f)
    t_ignores = t_data.get("userIgnoreFilters", [])
except Exception:
    t_ignores = ["graphify-out/", ".agents/", ".claude/", "node_modules/", ".venv/"]

p_data = {}
if os.path.exists(project_json):
    try:
        with open(project_json, "r") as f:
            p_data = json.load(f)
    except Exception:
        pass

p_ignores = p_data.get("userIgnoreFilters", [])
merged = list(p_ignores)
for ig in t_ignores:
    if ig not in merged:
        merged.append(ig)

p_data["userIgnoreFilters"] = merged
with open(project_json, "w") as f:
    json.dump(p_data, f, indent=2)
' "$PROJECT_APP_JSON" "$TEMPLATE_APP_JSON"

echo "✅ Игнорируемые файлы/папки в Obsidian обновлены."

echo ""
echo "================================================================="
echo "🎉 Готово! Агентская память подключена и готова к работе."
echo "================================================================="
echo "Для запуска циклов автоматизации:"
echo "  ./brain sleep            # Запустить Sleep Cycle"
echo "  ./brain check --report   # Выполнить Maintenance Check"
echo "  ./brain graphify         # Обновить граф знаний проекта"
echo "================================================================="
