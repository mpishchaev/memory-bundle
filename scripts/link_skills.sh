#!/usr/bin/env bash
set -e

# Скрипт интеграции централизованных навыков Единого Мозга (Single Source of Truth)
# Использование: ./link_skills.sh /путь/к/папке/навыков/агента
#
# Источник навыков определяется так:
#   1. переменная окружения BRAIN_SKILLS_DIR (если задана);
#   2. $BRAIN_ROOT/06_Skills (если задан BRAIN_ROOT);
#   3. 06_Skills рядом с каталогом скриптов (<хранилище>/05_Scripts/.. /06_Skills).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_ROOT="${BRAIN_ROOT:-$(dirname "$SCRIPT_DIR")}"
BRAIN_SKILLS_DIR="${BRAIN_SKILLS_DIR:-$VAULT_ROOT/06_Skills}"

if [ -z "$1" ]; then
    echo "❌ Ошибка: Не указан путь к целевой директории навыков агента/harness."
    echo "👉 Использование: $0 /путь/к/папке/skills"
    echo "Пример: $0 ~/.openclaw/workspace/skills"
    exit 1
fi

TARGET_DIR="${1%/}" # Убираем закрывающий слэш, если есть

if [ ! -d "$TARGET_DIR" ]; then
    echo "⚠️ Целевая директория '$TARGET_DIR' не найдена. Создаем..."
    mkdir -p "$TARGET_DIR"
fi

echo "🔄 Подключение единых когнитивных навыков из $BRAIN_SKILLS_DIR к $TARGET_DIR..."

SKILLS=("vault-sleep-cycle" "vault-maintenance" "vault-git-backup")

for SKILL in "${SKILLS[@]}"; do
    TARGET_SKILL_PATH="$TARGET_DIR/$SKILL"
    SOURCE_SKILL_PATH="$BRAIN_SKILLS_DIR/$SKILL"

    if [ ! -d "$SOURCE_SKILL_PATH" ]; then
        echo "❌ Ошибка: Исходный навык '$SOURCE_SKILL_PATH' не найден в ядре мозга!"
        echo "👉 Укажите корень хранилища через BRAIN_ROOT или BRAIN_SKILLS_DIR."
        exit 1
    fi

    # Если в целевой папке уже есть такой файл/папка или симлинк
    if [ -e "$TARGET_SKILL_PATH" ] || [ -L "$TARGET_SKILL_PATH" ]; then
        if [ -L "$TARGET_SKILL_PATH" ]; then
            echo "   - Обновление существующего симлинка для $SKILL..."
            rm "$TARGET_SKILL_PATH"
        else
            echo "   - Внимание: Найдена реальная копия '$SKILL'. Создаем резервную копию..."
            mv "$TARGET_SKILL_PATH" "${TARGET_SKILL_PATH}.bak_$(date +%s)"
        fi
    fi

    # Создаем символическую ссылку
    ln -s "$SOURCE_SKILL_PATH" "$TARGET_SKILL_PATH"
    echo "   ✅ Навык $SKILL успешно прилинкован."
done

echo ""
echo "🎉 Готово! Теперь среда агента использует единое мета-пространство хранилища."
echo "Все изменения в SKILL.md будут мгновенно синхронизированы между всеми harness."
