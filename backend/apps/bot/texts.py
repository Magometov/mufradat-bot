"""Тексты бота. Вынесены отдельно, чтобы править формулировки не трогая логику."""

ENTRY_FORMAT_HINT = """Формат:
<code>بَيْت | дом</code>
<code>بَيْت | дом | bayt</code>

Порядок частей не важен."""

ADMIN_WELCOME = ENTRY_FORMAT_HINT

USER_WELCOME = """السلام عليكم ورحمة الله وبركاته

Здесь наша общая колода арабских слов. Повторяешь карточками: каждое слово
возвращается тогда, когда ты вот-вот его забудешь.

Жми кнопку и начинай 👇"""

APP_NOT_READY = "السلام عليكم ورحمة الله وبركاته\n\nКарточки скоро откроются — загляни чуть позже."

ONLY_ADMIN_ADDS = "Колоду наполняет админ, а тебе остаётся приятное — учить 👇"

OPEN_APP_BUTTON = "Открыть карточки"


def added(arabic: str, translation: str, kind: str) -> str:
    return f"Добавлено ({kind.lower()}):\n<b>{arabic}</b> — {translation}"


def already_exists(arabic: str, translation: str) -> str:
    return f"Уже есть:\n<b>{arabic}</b> — {translation}"
