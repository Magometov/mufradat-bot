import logging

from aiogram import F, Router
from aiogram.types import Message
from asgiref.sync import sync_to_async
from django.db import transaction

from apps.bot import texts
from apps.bot.parsing import ParsedEntry, ParseError, parse_entry
from apps.bot.permissions import is_admin
from apps.vocabulary.kind import is_word
from apps.vocabulary.models import Number, Phrase, Word, WordForm

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

        created = await _store(parsed)
        card = texts.card_line(parsed.arabic, parsed.translation_ru)

        if created:
            logger.info("добавлено: %s — %s", parsed.arabic, parsed.translation_ru)
            added.append(card)
        else:
            existing.append(card)

    return texts.report(added, existing, failures)


@sync_to_async
@transaction.atomic
def _store(parsed: ParsedEntry) -> bool:
    """Кладёт карточку в свою таблицу и говорит, новая ли она.

    Слово заводится сразу с формой единственного числа, и обе строки пишутся одной
    транзакцией: слово без форм показывалось бы в админке пустой строкой. Отсюда и
    синхронная функция — обёртки транзакции для асинхронного кода в Django нет.

    Множественное число бот пока не принимает: формат строки его не различает, и
    дозаполняется оно в админке.
    """
    if not is_word(parsed.arabic, parsed.translation_ru):
        _, created = Phrase.objects.get_or_create(
            arabic=parsed.arabic,
            translation_ru=parsed.translation_ru,
            defaults={"transliteration": parsed.transliteration},
        )

        return created

    if WordForm.objects.filter(arabic=parsed.arabic, translation_ru=parsed.translation_ru).exists():
        return False

    WordForm.objects.create(
        word=Word.objects.create(),
        number=Number.SINGULAR,
        arabic=parsed.arabic,
        translation_ru=parsed.translation_ru,
        transliteration=parsed.transliteration,
    )

    return True
