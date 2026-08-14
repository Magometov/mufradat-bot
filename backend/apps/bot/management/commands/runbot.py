import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.bot.handlers import add, maintenance, start
from apps.bot.keyboards import menu_button


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
        # Заглушка идёт первой и берёт на себя всё: aiogram останавливается на первом
        # подошедшем обработчике, поэтому до разбора карточек дело не доходит.
        if settings.MAINTENANCE:
            dispatcher.include_router(maintenance.router)
        # Порядок важен: команды разбираются раньше свободного текста, иначе «/start»
        # уедет в разбор карточки.
        dispatcher.include_router(start.router)
        dispatcher.include_router(add.router)

        me = await bot.get_me()
        # Кнопка «Меню» задаётся у Telegram один раз и хранится на его стороне, поэтому
        # ставим её при каждом запуске: так адрес приложения не расходится с .env.
        await bot.set_chat_menu_button(menu_button=menu_button())
        state = " — ТЕХРАБОТЫ" if settings.MAINTENANCE else ""
        self.stdout.write(f"Бот @{me.username} запущен{state}")
        try:
            await dispatcher.start_polling(bot)
        finally:
            await bot.session.close()
