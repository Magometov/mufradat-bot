import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

from bot import api, config, keyboards, texts

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    """Приветствие, одно на всех; владельцу вслед — кнопки добавления.

    `ReplyKeyboardRemove` снимает клавиатуру, которую бот присылал раньше: Telegram
    держит её у себя, пока не уберут явно.
    """
    user = message.from_user

    if user is None:
        return

    logger.info("/start от %s (@%s)", user.id, user.username)
    body = texts.WELCOME if config.WEBAPP_URL else texts.APP_NOT_READY

    await message.answer(body, reply_markup=ReplyKeyboardRemove())

    # После ответа: журнал ждать человеку незачем, а бэкенд может и не отозваться.
    try:
        await api.log_visit(telegram_id=user.id, username=user.username or "")
    except api.BackendError as error:
        logger.warning("вход не записан: %s", error)

    if user.id == config.ADMIN_TELEGRAM_ID:
        await message.answer(texts.OWNER, reply_markup=keyboards.pick())
