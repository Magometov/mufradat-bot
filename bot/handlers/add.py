"""Добавление карточек владельцем: вставка, разбор, приёмка по одной, запись."""

import logging
from dataclasses import dataclass, replace
from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot import api, config, images, keyboards, parsing, texts
from bot.handlers import themes
from bot.parsing import Card, Group, Problem

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
SINGLE = {WORDS: parsing.one_word, PHRASES: parsing.one_phrase}
UNITS = {WORDS: "слов", PHRASES: "фраз"}
NUMBERS = {parsing.SINGULAR: "единственное", parsing.PLURAL: "множественное"}


@dataclass(slots=True)
class Pending:
    """Карточка в очереди на приёмку и номер её единицы: формы ложатся в одно слово."""

    card: Card
    unit: int


class Add(StatesGroup):
    """Чего диалог ждёт: строки, согласия, решения по карточке, промпта, правки."""

    lines = State()
    confirm = State()
    review = State()
    prompt = State()
    edit = State()


def _names(titles: list[str]) -> str:
    """Перечисление переводов в отчёте."""
    return ", ".join(f"«{escape(title)}»" for title in titles)


def _problems(problems: list[Problem]) -> str:
    """Беды строками: номер строки и причина."""
    return "\n".join(f"строка {problem.line}: {escape(problem.reason)}" for problem in problems)


def _preview(kind: str, groups: list[Group]) -> str:
    """Список разобранного: по строке на слово или фразу."""
    cards = [card for group in groups for card in group.cards]
    listing = "\n".join(
        f"{number}. {escape(group.title)}" for number, group in enumerate(groups, start=1)
    )
    text = texts.PREVIEW.format(
        units=UNITS[kind], found=len(groups), cards=len(cards), listing=listing
    )

    plain = sum(1 for card in cards if not card.prompt)

    return text if not plain else f"{text}\n\n{texts.PLAIN.format(plain=plain)}"


def _queue(groups: list[Group]) -> list[Pending]:
    """Разворачивает единицы в очередь карточек, помня, какая к какой единице."""
    return [Pending(card, unit) for unit, group in enumerate(groups) for card in group.cards]


def _caption(position: int, total: int, card: Card, reason: str) -> str:
    """Подпись карточки на приёмке: где мы, что это и чем нарисовано."""
    head = f"{position}/{total} · {escape(card.translation_ru)}"
    if card.number is not None:
        head = f"{head} · {NUMBERS[card.number]}"

    body = escape(card.arabic)
    if card.transliteration:
        body = f"{body} · {escape(card.transliteration)}"

    lines = [head, body]
    if card.prompt:
        lines.append(f"<i>{escape(card.prompt)}</i>")
    if reason:
        lines.append(texts.NO_DRAW.format(reason=escape(reason)))

    return "\n".join(lines)


async def _show(bot: Bot, chat: int, state: FSMContext) -> None:
    """Рисует картинку к первой карточке очереди и показывает её на приёмку."""
    data = await state.get_data()
    queue: list[Pending] = data["queue"]

    if not queue:
        await _finish(bot, chat, state)
        return

    card = queue[0].card
    image: bytes | None = None
    reason = ""

    if card.prompt:
        await bot.send_chat_action(chat, "upload_photo")
        try:
            image = await images.draw(card.prompt)
        except images.DrawFailed as error:
            reason = str(error)
            logger.warning("картинка не вышла: %s", error)

    await state.update_data(image=image)
    await state.set_state(Add.review)

    caption = _caption(data["done"] + 1, data["total"], card, reason)

    if image is None:
        await bot.send_message(chat, caption, reply_markup=keyboards.review())
        return

    await bot.send_photo(
        chat,
        BufferedInputFile(image, filename="card.jpg"),
        caption=caption,
        reply_markup=keyboards.review(),
    )


async def _store(state: FSMContext, image: bytes | None) -> None:
    """Пишет первую карточку очереди в колоду и считает исход."""
    data = await state.get_data()
    pending: Pending = data["queue"][0]
    card = pending.card
    words: dict[int, int] = data["words"]

    try:
        if data["kind"] == PHRASES:
            await api.add_phrase(
                arabic=card.arabic,
                translation_ru=card.translation_ru,
                transliteration=card.transliteration,
                image=image,
            )
        else:
            words[pending.unit] = await api.add_form(
                number=card.number or parsing.SINGULAR,
                arabic=card.arabic,
                translation_ru=card.translation_ru,
                transliteration=card.transliteration,
                word=words.get(pending.unit),
                image=image,
            )
    except api.Occupied:
        await state.update_data(skipped=[*data["skipped"], card.translation_ru])
        return

    await state.update_data(added=data["added"] + 1, words=words)


async def _advance(state: FSMContext) -> None:
    """Убирает решённую карточку из очереди."""
    data = await state.get_data()

    await state.update_data(queue=data["queue"][1:], done=data["done"] + 1, image=None)


async def _finish(bot: Bot, chat: int, state: FSMContext) -> None:
    """Отчитывается за партию и предлагает разобрать то, что лежало в разделе до неё."""
    data = await state.get_data()
    lesson: api.Lesson = data["lesson"]

    report = [texts.ADDED.format(added=data["added"])]
    if data["skipped"]:
        report.append(texts.SKIPPED.format(skipped=_names(data["skipped"])))
    if data["dropped"]:
        report.append(texts.DROPPED.format(dropped=_names(data["dropped"])))

    logger.info(
        "партия закрыта: добавлено %s, пропущено %s, отброшено %s",
        data["added"],
        len(data["skipped"]),
        len(data["dropped"]),
    )
    await state.clear()
    await bot.send_message(chat, "\n".join(report))

    if lesson.units:
        await themes.offer(bot, chat, state, lesson)


async def _broken(bot: Bot, chat: int, state: FSMContext, error: Exception) -> None:
    """Обрыв записи: дальше идти нельзя, но что легло — уже в колоде."""
    data = await state.get_data()

    logger.warning("запись оборвалась после %s карточек: %s", data["added"], error)
    await state.clear()
    await bot.send_message(
        chat, texts.BROKEN.format(reason=escape(str(error)), added=data["added"])
    )


@router.message(Command("add"))
async def handle_add(message: Message, state: FSMContext) -> None:
    """Начинает добавление командой — она же выход из брошенного диалога."""
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


async def _fresh(message: Message, groups: list[Group]) -> tuple[list[Group], list[str]]:
    """Отсеивает то, что уже в колоде. Бэкенд не ответил — идём как есть, с оговоркой."""
    pairs = [(card.arabic, card.translation_ru) for group in groups for card in group.cards]

    try:
        known = await api.known(pairs)
    except api.BackendError as error:
        logger.warning("колода не проверилась: %s", error)
        await message.answer(texts.DECK_UNREAD.format(reason=escape(str(error))))

        return groups, []

    return parsing.without_known(groups, known)


@router.message(Add.lines, ~CommandStart())
async def handle_lines(message: Message, state: FSMContext) -> None:
    """Разбирает вставку и показывает, что понял."""
    if not message.text:
        await message.answer(texts.WAITING)
        return

    data = await state.get_data()
    parsed = PARSERS[data["kind"]](message.text)

    if parsed.problems:
        await message.answer(texts.PROBLEMS.format(problems=_problems(parsed.problems)))
        return

    if not parsed.groups:
        await message.answer(texts.NOTHING)
        return

    groups, known = await _fresh(message, parsed.groups)

    if not groups:
        await state.clear()
        await message.answer(texts.ALL_KNOWN)
        return

    if known:
        await message.answer(texts.KNOWN.format(known=_names(known)))

    await state.update_data(groups=groups)
    await state.set_state(Add.confirm)
    await message.answer(_preview(data["kind"], groups), reply_markup=keyboards.confirm())


@router.callback_query(Add.confirm, F.data == keyboards.ADD_GO)
async def handle_go(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает приёмку: карточки идут по одной.

    Здесь же снимается список раздела — до первой записи, иначе новые карточки попали
    бы в разбор вместе со старыми.
    """
    data = await state.get_data()
    queue = _queue(data["groups"])

    await callback.answer()

    try:
        lesson = await api.lesson()
    except api.BackendError as error:
        lesson = api.Lesson(units=[], themes=[])
        logger.warning("раздел не прочитался: %s", error)
        await callback.bot.send_message(
            callback.from_user.id, texts.LESSON_UNREAD.format(reason=escape(str(error)))
        )

    await state.update_data(
        queue=queue,
        total=len(queue),
        done=0,
        words={},
        added=0,
        skipped=[],
        dropped=[],
        image=None,
        lesson=lesson,
    )
    await _show(callback.bot, callback.from_user.id, state)


@router.callback_query(Add.review, F.data.in_({keyboards.ADD_KEEP, keyboards.ADD_PLAIN}))
async def handle_keep(callback: CallbackQuery, state: FSMContext) -> None:
    """Кладёт карточку в колоду — с нарисованным или без него."""
    data = await state.get_data()
    image = data["image"] if callback.data == keyboards.ADD_KEEP else None

    await callback.answer()

    try:
        await _store(state, image)
    except api.BackendError as error:
        await _broken(callback.bot, callback.from_user.id, state, error)
        return

    await _advance(state)
    await _show(callback.bot, callback.from_user.id, state)


@router.callback_query(Add.review, F.data == keyboards.ADD_DROP)
async def handle_drop(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбрасывает карточку: в колоду она не пойдёт."""
    data = await state.get_data()
    pending: Pending = data["queue"][0]

    await state.update_data(dropped=[*data["dropped"], pending.card.translation_ru])
    await callback.answer()
    await _advance(state)
    await _show(callback.bot, callback.from_user.id, state)


@router.callback_query(Add.review, F.data == keyboards.ADD_REDRAW)
async def handle_redraw(callback: CallbackQuery, state: FSMContext) -> None:
    """Просит новый промпт: старый нарисовал не то."""
    await state.set_state(Add.prompt)
    await callback.answer()
    await callback.bot.send_message(callback.from_user.id, texts.NEW_PROMPT)


@router.message(Add.prompt, ~CommandStart())
async def handle_prompt(message: Message, state: FSMContext) -> None:
    """Рисует ту же карточку по новому промпту."""
    if not message.text:
        await message.answer(texts.WAITING)
        return

    data = await state.get_data()
    queue: list[Pending] = data["queue"]
    queue[0].card = replace(queue[0].card, prompt=message.text.strip())

    await state.update_data(queue=queue)
    await _show(message.bot, message.chat.id, state)


@router.callback_query(Add.review, F.data == keyboards.ADD_EDIT)
async def handle_edit(callback: CallbackQuery, state: FSMContext) -> None:
    """Просит строку заново: в самой карточке что-то не так."""
    await state.set_state(Add.edit)
    await callback.answer()
    await callback.bot.send_message(callback.from_user.id, texts.RESEND)


@router.message(Add.edit, ~CommandStart())
async def handle_resend(message: Message, state: FSMContext) -> None:
    """Заменяет карточку присланной строкой и рисует к ней заново."""
    if not message.text:
        await message.answer(texts.WAITING)
        return

    data = await state.get_data()

    try:
        card = SINGLE[data["kind"]](message.text)
    except parsing.Broken as error:
        await message.answer(texts.BAD_LINE.format(reason=escape(str(error))))
        return

    queue: list[Pending] = data["queue"]
    queue[0].card = card

    await state.update_data(queue=queue)
    await _show(message.bot, message.chat.id, state)


@router.callback_query(F.data == keyboards.ADD_CANCEL)
async def handle_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Бросает добавление. Что уже легло в колоду, там и остаётся."""
    await state.clear()
    await callback.answer()
    await callback.bot.send_message(callback.from_user.id, texts.CANCELLED)
