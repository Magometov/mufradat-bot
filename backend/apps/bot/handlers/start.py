import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from django.conf import settings

from apps.bot import texts
from apps.bot.permissions import is_admin

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    if message.from_user is None:
        return

    user = message.from_user
    logger.info("/start от %s (@%s)", user.id, user.username)

    # Приветствие — только текст: вход в приложение один на всех, синяя кнопка у поля
    # ввода. Она никуда не уезжает по истории, поэтому дублировать её в сообщении
    # незачем, а админу она нужна ровно так же, как ученику.
    if is_admin(user.id):
        await message.answer(texts.ADMIN_WELCOME)
        return

    await message.answer(texts.USER_WELCOME if settings.WEBAPP_URL else texts.APP_NOT_READY)
