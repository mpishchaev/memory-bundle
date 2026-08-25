#!/usr/bin/env bash
set -e

echo "================================================================="
echo "        Установка Obsidian Desktop & Настройка CLI               "
echo "================================================================="

# Функция проверки наличия команды
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

INSTALL_METHOD=""

if command_exists flatpak; then
    echo "[*] Обнаружен Flatpak. Установка Obsidian через Flathub..."
    # Проверяем, добавлен ли репозиторий flathub
    flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
    flatpak install -y flathub md.obsidian.Obsidian
    INSTALL_METHOD="flatpak"
elif command_exists snap; then
    echo "[*] Обнаружен Snap. Установка Obsidian из Snap Store..."
    sudo snap install obsidian --classic
    INSTALL_METHOD="snap"
else
    echo "[*] Ни Flatpak, ни Snap не обнаружены. Скачивание официального AppImage..."
    APPIMAGE_DIR="$HOME/Applications"
    mkdir -p "$APPIMAGE_DIR"
    APPIMAGE_PATH="$APPIMAGE_DIR/Obsidian.AppImage"
    
    # Получаем последнюю версию с GitHub
    LATEST_URL=$(curl -s https://api.github.com/repos/obsidianmd/obsidian-releases/releases/latest | grep "browser_download_url.*AppImage" | cut -d : -f 2,3 | tr -d \")
    
    if [ -z "$LATEST_URL" ]; then
        echo "[!] Не удалось автоматически определить URL AppImage. Скачивание базовой версии..."
        LATEST_URL="https://github.com/obsidianmd/obsidian-releases/releases/download/v1.16.7/Obsidian-1.16.7.AppImage"
    fi
    
    echo "Скачивание: $LATEST_URL"
    curl -L "$LATEST_URL" -o "$APPIMAGE_PATH"
    chmod +x "$APPIMAGE_PATH"
    echo "[+] AppImage сохранен в $APPIMAGE_PATH"
    INSTALL_METHOD="appimage"
fi

echo ""
echo "================================================================="
echo "                    ✅ УСТАНОВКА ЗАВЕРШЕНА                       "
echo "================================================================="
echo ""
echo "ВАЖНЫЕ ШАГИ ДЛЯ НАСТРОЙКИ CLI (Obsidian v1.12+):"
echo "1. Запустите Obsidian."
echo "2. Откройте или создайте хранилище (папка .brain в корне вашего проекта)."
echo "3. Перейдите в Настройки (Settings) -> Вкладка 'Общие' (General)."
echo "4. Найдите пункт 'Командный интерфейс' (Command-line interface / CLI)."
echo "5. Нажмите кнопку 'Включить' (Enable / Register) для интеграции команды 'obsidian' в терминал."
echo ""
echo "После этого вы сможете вызывать команды из терминала:"
echo "  obsidian open                 # Открыть запущенный инстанс"
echo "  obsidian commands             # Список доступных команд"
echo "================================================================="
