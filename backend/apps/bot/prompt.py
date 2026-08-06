from collections.abc import Callable

from apps.bot import texts
from apps.vocabulary.models import Entry

LIMIT = 100
# Лимит Telegram на текст сообщения.
MESSAGE_LIMIT = 4096


async def build_words_prompt() -> str:
    """Промпт на новые слова: что выучить дальше, глядя на пройденное."""
    return _fit(texts.AI_WORDS_HEAD, texts.meanings_block, await _meanings())


async def build_phrases_prompt() -> str:
    """Промпт на фразы из того, что группа уже знает."""
    return _fit(texts.AI_PHRASES_HEAD, texts.words_block, await _meanings())


async def _meanings() -> list[str]:
    """Переводы от новых к старым; id разрешает совпадение времени при пакетной вставке.

    Оба промпта показывают колоду переводами, без арабского: по решению владельца — так
    промпт чище и вчетверо короче.
    """
    queryset = Entry.objects.order_by("-created_at", "-id").values_list(
        "translation_ru", flat=True
    )[:LIMIT]

    return [translation async for translation in queryset]


def _fit(head: str, block: Callable[[int], str], meanings: list[str]) -> str:
    """Обрезает список с конца, пока сообщение не влезет в лимит Telegram.

    Первыми уходят самые старые: свежее для ИИ важнее. Сколько вошло, сказано в самом
    сообщении — «последние сто» это окно, и молча превращать его в «последние
    сколько-то» нельзя.
    """
    while len(_compose(head, block, meanings)) > MESSAGE_LIMIT and meanings:
        meanings.pop()

    return _compose(head, block, meanings)


def _compose(head: str, block: Callable[[int], str], meanings: list[str]) -> str:
    if not meanings:
        return f"{head}\n\n{texts.AI_PROMPT_EMPTY}"

    return f"{head}\n\n{block(len(meanings))}\n" + ", ".join(meanings)
