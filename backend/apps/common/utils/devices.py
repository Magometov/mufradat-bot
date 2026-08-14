"""Устройство словами из строки браузера. Точной модели User-Agent не сообщает."""

from collections.abc import Sequence

# Порядок важен: у Chrome в строке есть слово Safari, у Edge и Яндекса — Chrome.
SYSTEMS = (
    ("iPhone", "iPhone"),
    ("iPad", "iPad"),
    ("Android", "Android"),
    ("Macintosh", "Mac"),
    ("Windows", "Windows"),
    ("Linux", "Linux"),
)
BROWSERS = (
    ("YaBrowser", "Яндекс"),
    ("Edg/", "Edge"),
    ("OPR/", "Opera"),
    ("Chrome", "Chrome"),
    ("Firefox", "Firefox"),
    ("Safari", "Safari"),
)


def device_name(user_agent: str) -> str:
    """Собирает «iPhone · Safari». Чего в строке не нашлось, то опускает."""
    found = (_first(user_agent, SYSTEMS), _first(user_agent, BROWSERS))

    return " · ".join(part for part in found if part)


def _first(user_agent: str, marks: Sequence[tuple[str, str]]) -> str:
    """Первая подошедшая примета: они идут от частной к общей."""
    return next((label for mark, label in marks if mark in user_agent), "")
