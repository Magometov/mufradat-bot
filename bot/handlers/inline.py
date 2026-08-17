"""Карточка из колоды в любой чат: `@бот слово` и выбор из найденного."""

import logging

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.types import (
    InlineQuery,
    InlineQueryResult,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
)

from bot import api, cards, texts

logger = logging.getLogger(__name__)

router = Router()

# Столько Telegram держит ответ у себя. Запрос на каждую набранную букву кэш всё равно
# не ловит — строки разные, — а свежесть колоды важнее: слово добавили и сразу шлют.
CACHE = 60


def _caption(card: api.Found) -> str:
    """Что уедет в чат: арабское, перевод, транслитерация."""
    return cards.caption(
        texts.INLINE_CARD,
        arabic=card.arabic,
        translation=card.translation_ru,
        transliteration=card.transliteration,
    )


def as_result(card: api.Found) -> InlineQueryResult:
    """Одна строка в списке выбора. Без картинки карточка уезжает текстом."""
    text = _caption(card)

    if card.image is None:
        return InlineQueryResultArticle(
            id=card.id,
            title=card.translation_ru,
            description=card.arabic,
            input_message_content=InputTextMessageContent(
                message_text=text, parse_mode=ParseMode.HTML
            ),
        )

    return InlineQueryResultPhoto(
        id=card.id,
        photo_url=card.image,
        thumbnail_url=card.image,
        title=card.translation_ru,
        description=card.arabic,
        caption=text,
        parse_mode=ParseMode.HTML,
    )


@router.inline_query()
async def handle_inline(query: InlineQuery) -> None:
    """Ищет по колоде и показывает найденное. Открыт всем: колода и так открыта."""
    try:
        found = await api.search(query.query.strip())
    except api.BackendError as error:
        # Отвечаем и на отказ: без ответа список выбора висит с прошлым запросом.
        # Без кэша — чтобы следующая буква спросила заново, а не получила ту же пустоту.
        logger.warning("поиск не ответил: %s", error)
        await query.answer([], cache_time=0)

        return

    await query.answer([as_result(card) for card in found], cache_time=CACHE)
