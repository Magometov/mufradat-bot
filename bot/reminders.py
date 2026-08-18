"""Напоминания в чат: бот спрашивает бэкенд и отправляет то, что тот отдал."""

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from bot import api, cards, group, texts

logger = logging.getLogger(__name__)

# Как часто бот спрашивает бэкенд. Шаг между сообщениями и окно тишины решает он же,
# поэтому лишний вопрос ничего не рассылает.
EVERY = 300

# Столько ждём после сбоя: бэкенд мог перезапускаться при выкладке.
AFTER_ERROR = 60


def _caption(card: api.Reminder) -> str:
    """Карточка словами: нужна только там, где картинки нет."""
    return cards.caption(
        texts.REMINDER_CARD,
        arabic=card.arabic,
        translation=card.translation_ru,
        transliteration=card.transliteration,
    )


async def _deliver(bot: Bot, card: api.Reminder) -> None:
    """Отправляет одну карточку. Подписи под картинкой нет: слова нарисованы на ней."""
    if card.image is None:
        await bot.send_message(card.telegram_id, _caption(card))
        return

    await bot.send_photo(card.telegram_id, card.image)


async def _round(bot: Bot) -> None:
    """Один обход: напоминания по личным чатам и, если наступил слот, слово в группу."""
    cards = await api.reminders()

    for card in cards:
        try:
            await _deliver(bot, card)
        except TelegramForbiddenError:
            # Человек заблокировал бота: жаловаться некому, и это не повод падать.
            logger.info("напоминание не доставлено, чат закрыт: %s", card.telegram_id)
        except Exception:
            logger.exception("напоминание не отправилось: %s", card.telegram_id)

    await group.send(bot)


async def run(bot: Bot) -> None:
    """Спрашивает бэкенд по кругу. Живёт рядом с long polling, своего расписания не имеет."""
    logger.info("напоминания включены, опрос каждые %s секунд", EVERY)

    while True:
        try:
            await _round(bot)
            await asyncio.sleep(EVERY)
        except asyncio.CancelledError:
            raise
        except api.BackendError as error:
            logger.warning("бэкенд не ответил про напоминания: %s", error)
            await asyncio.sleep(AFTER_ERROR)
        except Exception:
            logger.exception("обход напоминаний сорвался")
            await asyncio.sleep(AFTER_ERROR)
