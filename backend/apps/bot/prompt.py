from apps.bot import texts
from apps.vocabulary.enums import Kind
from apps.vocabulary.models import Entry

WORDS = 100
PHRASES = 10
# Лимит Telegram на текст сообщения.
MESSAGE_LIMIT = 4096


async def build_prompt() -> str:
    """Собирает сообщение для ИИ: инструкция плюс то, что группа уже знает.

    Список набирается от новых записей к старым и обрезается по лимиту Telegram.
    Сколько слов вошло, сказано в самом сообщении: «последние сто» — это окно, и
    молча превращать его в «последние сколько-то» нельзя.
    """
    words = await _lines(Kind.WORD, WORDS)
    phrases = await _lines(Kind.PHRASE, PHRASES)

    while len(_compose(words, phrases)) > MESSAGE_LIMIT and (words or phrases):
        # Первыми уходят самые старые слова, фразы режутся последними: их мало,
        # а стиль модель ловит именно по ним.
        (words or phrases).pop()

    return _compose(words, phrases)


async def _lines(kind: Kind, limit: int) -> list[str]:
    """Записи от новых к старым; id разрешает совпадение времени при пакетной вставке."""
    queryset = Entry.objects.filter(kind=kind).order_by("-created_at", "-id")[:limit]
    return [f"{entry.arabic} — {entry.translation_ru}" async for entry in queryset]


def _compose(words: list[str], phrases: list[str]) -> str:
    blocks = [texts.AI_PROMPT_HEAD]

    if words:
        blocks.append(texts.words_block(len(words)) + "\n" + "\n".join(words))
    if phrases:
        blocks.append(texts.phrases_block(len(phrases)) + "\n" + "\n".join(phrases))
    if not words and not phrases:
        blocks.append(texts.AI_PROMPT_EMPTY)

    return "\n\n".join(blocks)
