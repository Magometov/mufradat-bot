from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from apps.bot import texts
from apps.bot.keyboards import open_app
from apps.bot.permissions import is_admin

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    if message.from_user is None:
        return

    if is_admin(message.from_user.id):
        await message.answer(texts.ADMIN_WELCOME)
        return

    keyboard = open_app()
    body = texts.USER_WELCOME if keyboard else texts.APP_NOT_READY
    await message.answer(body + texts.your_id(message.from_user.id), reply_markup=keyboard)
