import logging

from aiogram import Router
from aiogram.types import Message

from apps.bot import texts

logger = logging.getLogger(__name__)

router = Router()


@router.message()
async def handle_any(message: Message) -> None:
    """Отвечает на всё одним сообщением, включая команды и админа.

    Админа не пропускаем нарочно: работы идут как раз в базе, и добавленная карточка
    легла бы в схему, которая в этот момент переезжает.
    """
    if message.from_user is not None:
        logger.info("техработы: сообщение от %s", message.from_user.id)

    await message.answer(texts.MAINTENANCE)
