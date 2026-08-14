"""Запуск бота: long polling."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError

from bot import config
from bot.handlers import maintenance, start
from bot.keyboards import menu_button

logger = logging.getLogger(__name__)


async def run(token: str) -> None:
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    # Заглушка первой: aiogram останавливается на первом подошедшем обработчике.
    dispatcher.include_router(maintenance.router)
    dispatcher.include_router(start.router)

    # Сессию закрываем и когда запуск не удался: иначе aiogram ругается на брошенное
    # соединение, а настоящая причина теряется в этом шуме.
    try:
        me = await bot.get_me()
        await bot.set_chat_menu_button(menu_button=menu_button())
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

    asyncio.run(run(config.BOT_TOKEN))


if __name__ == "__main__":
    main()
