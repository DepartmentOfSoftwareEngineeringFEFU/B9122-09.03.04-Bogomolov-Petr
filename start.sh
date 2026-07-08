#!/usr/bin/env bash
# Запуск бэкенда (Django) и Telegram-бота из Git Bash / MSYS.
# Использование: ./start.sh          — backend + bot
#                ./start.sh --no-bot — только backend
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PY="$ROOT/.venv/bin/python.exe"
NO_BOT=false
[ "$1" = "--no-bot" ] && NO_BOT=true

echo "=== School Manager ==="

if [ ! -f "$ROOT/.env" ]; then
    echo "WARNING: .env не найден. Скопируйте .env.example в .env и укажите TELEGRAM_BOT_TOKEN."
fi

if [ ! -x "$VENV_PY" ]; then
    echo "Создаю виртуальное окружение..."
    python -m venv "$ROOT/.venv"
fi

echo "Устанавливаю зависимости..."
"$VENV_PY" -m pip install -q -r "$ROOT/backend/requirements.txt"
"$VENV_PY" -m pip install -q -r "$ROOT/bot/requirements.txt"

echo "Применяю миграции..."
(cd "$ROOT/backend" && "$VENV_PY" manage.py migrate --noinput)

echo ""
echo "Запускаю Django на http://localhost:8000 ..."
(cd "$ROOT/backend" && "$VENV_PY" manage.py runserver 0.0.0.0:8000) &
DJANGO_PID=$!

if [ "$NO_BOT" = false ]; then
    sleep 1
    echo "Запускаю Telegram-бота..."
    (cd "$ROOT" && "$VENV_PY" bot/bot.py) &
    BOT_PID=$!
fi

echo ""
echo "=== Сервисы ==="
echo "  Web:   http://localhost:8000"
echo "  Admin: http://localhost:8000/admin/"
echo "  API:   http://localhost:8000/api/"
echo ""
echo "Ctrl+C для остановки."

cleanup() {
    echo ""
    echo "Останавливаю сервисы..."
    kill "$DJANGO_PID" 2>/dev/null || true
    [ -n "$BOT_PID" ] && kill "$BOT_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait "$DJANGO_PID"
