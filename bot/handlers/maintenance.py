import logging

from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove

from bot import config, texts

logger = logging.getLogger(__name__)

router = Router()


def is_on(message: Message) -> bool:
    """Идут ли работы. Проверяется на каждом сообщении: признак снимают файлом."""
    return config.MAINTENANCE_FLAG.exists()


@router.message(is_on)
async def handle_any(message: Message) -> None:
    """Отвечает на всё одним сообщением, включая команды.

    Клавиатуру снимает тоже: под заглушкой до `/start` дело не доходит, а старые
    кнопки Telegram держит у себя, пока их не уберут явно.
    """
    if message.from_user is not None:
        logger.info("техработы: сообщение от %s", message.from_user.id)

    await message.answer(texts.MAINTENANCE, reply_markup=ReplyKeyboardRemove())
