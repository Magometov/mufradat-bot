"""Тексты бота. Вынесены отдельно, чтобы править формулировки не трогая логику."""

from aiogram import html

ENTRY_FORMAT_HINT = """Формат:
<code>بَيْت | дом</code>
<code>بَيْت | дом | bayt</code>

Порядок частей не важен. Карточек может быть сколько угодно — каждая на своей строке."""

# Сообщение Telegram — 4096 знаков, поэтому длинные списки в отчёте подрезаются.
LIST_LIMIT = 30

ADMIN_WELCOME = ENTRY_FORMAT_HINT

USER_WELCOME = """السلام عليكم ورحمة الله وبركاته

Карточка приходит случайной стороной — то арабским вперёд, то русским:
вспоминаешь, переворачиваешь и проверяешь себя.

Жми «Карточки» слева от поля ввода и начинай 👇"""

APP_NOT_READY = "السلام عليكم ورحمة الله وبركاته\n\nКарточки скоро откроются — загляни чуть позже."

ONLY_ADMIN_ADDS = "Колоду наполняет админ, а тебе остаётся приятное — учить 👇"

MAINTENANCE = """السلام عليكم ورحمة الله وبركاته

Идут технические работы: колода переезжает на новый лад.

Карточки скоро вернутся — загляни чуть позже 🙏"""

# Подпись синей кнопки у поля ввода: она заменяет слово «Меню», поэтому короткая.
# Приветствие называет её по имени, поэтому переименование — это две правки, не одна.
MENU_BUTTON = "Карточки"


def card_line(arabic: str, translation: str) -> str:
    """Карточка в отчёте. Текст экранируется: разметка сообщения — HTML, а строка
    приходит от человека и может содержать «<»."""
    return f"<b>{html.quote(arabic)}</b> — {html.quote(translation)}"


def failure_line(line: str, reason: str) -> str:
    """Непонятая строка возвращается целиком: так её видно точнее, чем по номеру."""
    return f"<code>{html.quote(line)}</code>\n{html.quote(reason)}"


def report(added: list[str], existing: list[str], failures: list[str]) -> str:
    """Отчёт по всему сообщению: что добавлено, что уже было, что не разобралось."""
    blocks = []

    if added:
        blocks.append(_block(f"Добавлено {len(added)}:", added))
    if existing:
        blocks.append(_block(f"Уже есть {len(existing)}:", existing))
    if failures:
        blocks.append(_block(f"Не разобрал {len(failures)}:", failures))
        blocks.append(ENTRY_FORMAT_HINT)

    return "\n\n".join(blocks)


def _block(head: str, lines: list[str]) -> str:
    shown = lines[:LIST_LIMIT]
    hidden = len(lines) - len(shown)
    tail = f"\nи ещё {hidden}" if hidden else ""

    return f"{head}\n" + "\n".join(shown) + tail
