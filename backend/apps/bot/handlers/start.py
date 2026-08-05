import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from apps.bot import texts
from apps.bot.keyboards import open_app
from apps.bot.permissions import is_admin

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    if message.from_user is None:
        return

    user = message.from_user
    # В логе видно, кто подключился; оттуда же берётся ID для ADMIN_TELEGRAM_IDS.
    logger.info("/start от %s (@%s)", user.id, user.username)

    if is_admin(user.id):
        await message.answer(texts.ADMIN_WELCOME)
        return

    keyboard = open_app()
    body = texts.USER_WELCOME if keyboard else texts.APP_NOT_READY
    await message.answer(body, reply_markup=keyboard)
