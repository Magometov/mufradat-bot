import logging

from aiogram import F, Router
from aiogram.types import Message

from apps.bot import texts
from apps.bot.keyboards import open_app
from apps.bot.parsing import ParsedEntry, ParseError, parse_entry
from apps.bot.permissions import is_admin
from apps.vocabulary.models import Entry

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    if not is_admin(message.from_user.id):
        await message.answer(texts.ONLY_ADMIN_ADDS, reply_markup=open_app())
        return

    try:
        parsed = parse_entry(message.text)
    except ParseError as error:
        await message.answer(f"{error}\n\n{texts.ENTRY_FORMAT_HINT}")
        return

    await _save(message, parsed)


async def _save(message: Message, parsed: ParsedEntry) -> None:
    entry, created = await Entry.objects.aget_or_create(
        arabic=parsed.arabic,
        translation_ru=parsed.translation_ru,
        defaults={"kind": parsed.kind, "transliteration": parsed.transliteration},
    )

    if not created:
        await message.answer(texts.already_exists(entry.arabic, entry.translation_ru))
        return

    logger.info("добавлено: %s — %s", entry.arabic, entry.translation_ru)
    await message.answer(texts.added(entry.arabic, entry.translation_ru, entry.get_kind_display()))
