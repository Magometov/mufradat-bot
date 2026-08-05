import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.bot.handlers import start


class Command(BaseCommand):
    help = "Запустить телеграм-бота (long polling)"

    def handle(self, *args: object, **options: object) -> None:
        if not settings.BOT_TOKEN:
            raise CommandError("BOT_TOKEN не задан. Создай бота у @BotFather и впиши токен в .env")
        if not settings.ADMIN_TELEGRAM_ID:
            self.stdout.write("ADMIN_TELEGRAM_ID не задан — админского приветствия не будет.")

        asyncio.run(self._run())

    async def _run(self) -> None:
        bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dispatcher = Dispatcher()
        dispatcher.include_router(start.router)

        me = await bot.get_me()
        self.stdout.write(f"Бот @{me.username} запущен")
        try:
            await dispatcher.start_polling(bot)
        finally:
            await bot.session.close()
