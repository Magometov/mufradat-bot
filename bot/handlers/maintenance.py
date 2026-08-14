import logging

from aiogram import Router
from aiogram.types import Message

from bot import config, texts

logger = logging.getLogger(__name__)

router = Router()


def is_on(message: Message) -> bool:
    """Идут ли работы. Проверяется на каждом сообщении: признак снимают файлом."""
    return config.MAINTENANCE_FLAG.exists()


@router.message(is_on)
async def handle_any(message: Message) -> None:
    """Отвечает на всё одним сообщением, включая команды."""
    if message.from_user is not None:
        logger.info("техработы: сообщение от %s", message.from_user.id)

    await message.answer(texts.MAINTENANCE)
