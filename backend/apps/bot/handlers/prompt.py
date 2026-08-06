import logging
from collections.abc import Awaitable, Callable

from aiogram import F, Router
from aiogram.types import Message

from apps.bot import texts
from apps.bot.keyboards import open_app
from apps.bot.permissions import is_admin
from apps.bot.prompt import build_phrases_prompt, build_words_prompt

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == texts.AI_WORDS_BUTTON)
async def handle_words(message: Message) -> None:
    await _send(message, build_words_prompt, "слова")


@router.message(F.text == texts.AI_PHRASES_BUTTON)
async def handle_phrases(message: Message) -> None:
    await _send(message, build_phrases_prompt, "фразы")


async def _send(
    message: Message,
    build: Callable[[], Awaitable[str]],
    label: str,
) -> None:
    """Отдаёт промпт админу; остальным — отказ с кнопкой приложения."""
    if message.from_user is None:
        return

    if not is_admin(message.from_user.id):
        await message.answer(texts.ONLY_ADMIN_ADDS, reply_markup=open_app())
        return

    prompt = await build()
    logger.info("промпт (%s): %d знаков", label, len(prompt))
    # Без разметки: в тексте есть «|» и арабский, а сообщение уходит на копирование.
    await message.answer(prompt, parse_mode=None)
