import logging

from aiogram import F, Router
from aiogram.types import Message

from apps.bot import texts
from apps.bot.parsing import ParseError, parse_entry
from apps.bot.permissions import is_admin
from apps.vocabulary.kind import is_word
from apps.vocabulary.models import Entry

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    if not is_admin(message.from_user.id):
        await message.answer(texts.ONLY_ADMIN_ADDS)
        return

    lines = [line.strip() for line in message.text.splitlines()]
    lines = [line for line in lines if line]

    if not lines:
        await message.answer(texts.ENTRY_FORMAT_HINT)
        return

    await message.answer(await _save(lines))


async def _save(lines: list[str]) -> str:
    """Сохраняет каждую строку и собирает отчёт по всему сообщению.

    Одна плохая строка не отменяет остальные: список от ИИ приходит целиком, и
    переписывать его из-за одной опечатки незачем — вернуть надо именно её.
    """
    added: list[str] = []
    existing: list[str] = []
    failures: list[str] = []

    for line in lines:
        try:
            parsed = parse_entry(line)
        except ParseError as error:
            failures.append(texts.failure_line(line, str(error)))
            continue

        entry, created = await Entry.objects.aget_or_create(
            arabic=parsed.arabic,
            translation_ru=parsed.translation_ru,
            defaults={
                "transliteration": parsed.transliteration,
                "is_word": is_word(parsed.arabic, parsed.translation_ru),
            },
        )
        card = texts.card_line(entry.arabic, entry.translation_ru)

        if created:
            logger.info("добавлено: %s — %s", entry.arabic, entry.translation_ru)
            added.append(card)
        else:
            existing.append(card)

    return texts.report(added, existing, failures)
