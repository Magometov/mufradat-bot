"""Запуск бота: long polling."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.types import BotCommand, BotCommandScopeChat

from bot import config
from bot.handlers import add, maintenance, start, themes
from bot.keyboards import menu_button

logger = logging.getLogger(__name__)


async def set_commands(bot: Bot) -> None:
    """Команда добавления стоит в меню только у владельца, остальным её нет."""
    if not config.ADMIN_TELEGRAM_ID:
        return

    await bot.set_my_commands(
        [BotCommand(command="add", description="Добавить слова или фразы")],
        scope=BotCommandScopeChat(chat_id=config.ADMIN_TELEGRAM_ID),
    )


async def run(token: str) -> None:
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    # Заглушка первой: aiogram останавливается на первом подошедшем обработчике.
    dispatcher.include_router(maintenance.router)
    dispatcher.include_router(add.router)
    dispatcher.include_router(themes.router)
    dispatcher.include_router(start.router)

    # Сессию закрываем и когда запуск не удался: иначе aiogram ругается на брошенное
    # соединение, а настоящая причина теряется в этом шуме.
    try:
        me = await bot.get_me()
        await bot.set_chat_menu_button(menu_button=menu_button())
        await set_commands(bot)
        logger.info("бот @%s запущен", me.username)
        await dispatcher.start_polling(bot)
    except TelegramUnauthorizedError:
        raise SystemExit("BOT_TOKEN не принят Telegram — проверь токен в .env") from None
    finally:
        await bot.session.close()


def main() -> None:
    config.setup_logging()

    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN не задан. Создай бота у @BotFather и впиши токен в .env")
    if not config.WEBAPP_URL:
        logger.warning("WEBAPP_URL не задан — кнопки «Карточки» у поля ввода не будет")
    if not config.ADMIN_TELEGRAM_ID:
        logger.warning("ADMIN_TELEGRAM_ID не задан — добавлять карточки будет некому")
    if not config.BOT_API_TOKEN:
        logger.warning("BOT_API_TOKEN не задан — бэкенд не примет ни одной карточки")

    asyncio.run(run(config.BOT_TOKEN))


if __name__ == "__main__":
    main()
