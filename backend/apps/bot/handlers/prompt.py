import logging

from aiogram import F, Router
from aiogram.types import Message

from apps.bot import texts
from apps.bot.keyboards import open_app
from apps.bot.permissions import is_admin
from apps.bot.prompt import build_prompt

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == texts.AI_PROMPT_BUTTON)
async def handle_prompt(message: Message) -> None:
    if message.from_user is None:
        return

    if not is_admin(message.from_user.id):
        await message.answer(texts.ONLY_ADMIN_ADDS, reply_markup=open_app())
        return

    prompt = await build_prompt()
    logger.info("промпт для ИИ: %d знаков", len(prompt))
    # Без разметки: в тексте есть «|» и арабский, а сообщение уходит на копирование.
    await message.answer(prompt, parse_mode=None)
