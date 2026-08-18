"""Слово в группу: бэкенд решает, пора ли и какое, бот отправляет."""

import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError

from bot import api, cards, config, texts

logger = logging.getLogger(__name__)


def _caption(card: api.GroupCard) -> str:
    """Карточка целиком: арабское, перевод, транслитерация."""
    return cards.caption(
        texts.GROUP_CARD,
        arabic=card.arabic,
        translation=card.translation_ru,
        transliteration=card.transliteration,
    )


async def _deliver(bot: Bot, card: api.GroupCard) -> None:
    """Отправляет карточку в группу. Подписи под картинкой нет: слова нарисованы на ней."""
    if card.image is None:
        await bot.send_message(card.chat_id, _caption(card))
        return

    await bot.send_photo(card.chat_id, card.image)


async def send(bot: Bot, *, forced: bool = False) -> api.GroupCard | None:
    """Спрашивает слово для группы и отправляет то, что дали. `None` — не ушло ничего."""
    card = await api.group_card(forced=forced)

    if card is None:
        return None

    try:
        await _deliver(bot, card)
    except TelegramForbiddenError:
        # Бота выгнали из группы: жаловаться некому, и это не повод падать.
        logger.info("слово в группу не доставлено, чат закрыт: %s", card.chat_id)
        return None
    except Exception:
        logger.exception("слово в группу не отправилось: %s", card.chat_id)
        return None

    return card


async def _once() -> None:
    """Одна отправка своей сессией: рядом с работающим ботом это второй, короткий клиент."""
    bot = Bot(token=config.BOT_TOKEN or "", default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    try:
        card = await send(bot, forced=True)
    except api.BackendError as error:
        raise SystemExit(f"бэкенд не ответил: {error}") from None
    finally:
        await bot.session.close()

    if card is None:
        logger.warning("в группу ничего не ушло: группа не задана или в колоде нет слов")

        return

    logger.info("отправил в группу: %s", card.translation_ru)


def main() -> None:
    """Разовая отправка из оболочки: `docker compose exec bot python -m bot.group`."""
    config.setup_logging()

    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN не задан — отправлять нечем")

    asyncio.run(_once())


if __name__ == "__main__":
    main()
