"""Настройки бота из окружения."""

import logging
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")
ADMIN_TELEGRAM_ID = int(getenv("ADMIN_TELEGRAM_ID") or 0)
WEBAPP_URL = getenv("WEBAPP_URL")
MAINTENANCE_FLAG = Path(getenv("MAINTENANCE_FLAG", "/flags/maintenance"))

# Куда бот складывает карточки: служебные ручки бэкенда и общий с ним секрет.
BACKEND_URL = getenv("BACKEND_URL", "http://backend:8000").rstrip("/")
BOT_API_TOKEN = getenv("BOT_API_TOKEN")


def setup_logging() -> None:
    """Формат тот же, что у бэкенда."""
    logging.basicConfig(
        level=logging.INFO,
        format="{asctime} {levelname} {name}: {message}",
        style="{",
    )
