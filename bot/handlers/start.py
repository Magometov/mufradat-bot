import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

from bot import config, texts

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    """Приветствие, одно на всех.

    `ReplyKeyboardRemove` снимает клавиатуру, которую бот присылал раньше: Telegram
    держит её у себя, пока не уберут явно.
    """
    if message.from_user is None:
        return

    logger.info("/start от %s (@%s)", message.from_user.id, message.from_user.username)
    body = texts.WELCOME if config.WEBAPP_URL else texts.APP_NOT_READY

    await message.answer(body, reply_markup=ReplyKeyboardRemove())
