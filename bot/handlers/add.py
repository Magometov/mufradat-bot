"""Добавление карточек владельцем: вставка, разбор, подтверждение, запись."""

import logging
from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import api, config, keyboards, parsing, texts
from bot.parsing import Group, Problem

logger = logging.getLogger(__name__)

router = Router()
# Колоду наполняет только владелец: посторонние сюда не попадают вовсе.
router.message.filter(F.from_user.id == config.ADMIN_TELEGRAM_ID)
router.callback_query.filter(F.from_user.id == config.ADMIN_TELEGRAM_ID)

WORDS = "words"
PHRASES = "phrases"

KINDS = {keyboards.ADD_WORDS: WORDS, keyboards.ADD_PHRASES: PHRASES}
FORMATS = {WORDS: texts.WORDS_FORMAT, PHRASES: texts.PHRASES_FORMAT}
PARSERS = {WORDS: parsing.parse_words, PHRASES: parsing.parse_phrases}
UNITS = {WORDS: "слов", PHRASES: "фраз"}


class Add(StatesGroup):
    """Чего диалог ждёт: сначала строки, потом согласие на запись."""

    lines = State()
    confirm = State()


async def _answer(callback: CallbackQuery, text: str) -> None:
    """Отвечает в тот же чат: сообщение с кнопкой боту могло стать недоступным."""
    await callback.bot.send_message(callback.from_user.id, text)


def _problems(problems: list[Problem]) -> str:
    """Беды строками: номер строки и причина."""
    return "\n".join(f"строка {problem.line}: {escape(problem.reason)}" for problem in problems)


def _preview(kind: str, groups: list[Group]) -> str:
    """Список разобранного: по строке на слово или фразу."""
    listing = "\n".join(
        f"{number}. {escape(group.title)}" for number, group in enumerate(groups, start=1)
    )

    return texts.PREVIEW.format(
        units=UNITS[kind],
        found=len(groups),
        cards=sum(len(group.cards) for group in groups),
        listing=listing,
    )


async def _write(kind: str, group: Group) -> tuple[int, list[str]]:
    """Пишет карточки одной единицы. Формы одного слова цепляются к одному номеру."""
    written = 0
    skipped: list[str] = []
    word: int | None = None

    for card in group.cards:
        try:
            if kind == PHRASES:
                await api.add_phrase(
                    arabic=card.arabic,
                    translation_ru=card.translation_ru,
                    transliteration=card.transliteration,
                )
            else:
                word = await api.add_form(
                    number=card.number or parsing.SINGULAR,
                    arabic=card.arabic,
                    translation_ru=card.translation_ru,
                    transliteration=card.transliteration,
                    word=word,
                )
        except api.Occupied:
            skipped.append(card.translation_ru)
            continue

        written += 1

    return written, skipped


@router.message(Command("add"))
async def handle_add(message: Message, state: FSMContext) -> None:
    """Начинает добавление командой — на случай, когда приветствие уже уехало вверх."""
    await state.clear()
    await message.answer(texts.PICK, reply_markup=keyboards.pick())


@router.callback_query(F.data.in_(KINDS))
async def handle_kind(callback: CallbackQuery, state: FSMContext) -> None:
    """Запоминает, что добавляем, и присылает формат."""
    kind = KINDS[callback.data or ""]

    await state.set_state(Add.lines)
    await state.update_data(kind=kind)
    await callback.answer()
    await callback.bot.send_message(
        callback.from_user.id, FORMATS[kind], reply_markup=keyboards.cancel()
    )


@router.message(Add.lines, ~CommandStart())
async def handle_lines(message: Message, state: FSMContext) -> None:
    """Разбирает вставку и показывает, что понял."""
    if not message.text:
        await message.answer(texts.WAITING)
        return

    data = await state.get_data()
    kind = data["kind"]
    parsed = PARSERS[kind](message.text)

    if parsed.problems:
        await message.answer(texts.PROBLEMS.format(problems=_problems(parsed.problems)))
        return

    if not parsed.groups:
        await message.answer(texts.NOTHING)
        return

    await state.update_data(groups=parsed.groups)
    await state.set_state(Add.confirm)
    await message.answer(_preview(kind, parsed.groups), reply_markup=keyboards.confirm())


@router.callback_query(Add.confirm, F.data == keyboards.ADD_GO)
async def handle_go(callback: CallbackQuery, state: FSMContext) -> None:
    """Пишет разобранное в колоду и отчитывается."""
    data = await state.get_data()
    kind: str = data["kind"]
    groups: list[Group] = data["groups"]

    await state.clear()
    await callback.answer()

    added = 0
    skipped: list[str] = []

    try:
        for group in groups:
            written, occupied = await _write(kind, group)
            added += written
            skipped += occupied
    except api.BackendError as error:
        logger.warning("запись оборвалась после %s карточек: %s", added, error)
        await _answer(callback, texts.BROKEN.format(reason=escape(str(error)), added=added))
        return

    logger.info("владелец добавил карточек: %s, пропущено: %s", added, len(skipped))

    report = [texts.ADDED.format(added=added)]
    if skipped:
        names = ", ".join(f"«{escape(name)}»" for name in skipped)
        report.append(texts.SKIPPED.format(skipped=names))
    report.append(texts.NO_PICTURES)

    await _answer(callback, "\n".join(report))


@router.callback_query(F.data == keyboards.ADD_CANCEL)
async def handle_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Бросает добавление из любого места диалога."""
    await state.clear()
    await callback.answer()
    await _answer(callback, texts.CANCELLED)
