"""Разбор раздела последнего урока: что в нём осталось — по темам, по одному."""

import logging
from html import escape

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery

from bot import api, config, keyboards, texts

logger = logging.getLogger(__name__)

router = Router()
# Колоду правит только владелец.
router.callback_query.filter(F.from_user.id == config.ADMIN_TELEGRAM_ID)


class Sort(StatesGroup):
    """Сначала спрашиваем, разбирать ли сейчас, потом идём по единицам."""

    offer = State()
    walk = State()


async def offer(bot: Bot, chat: int, state: FSMContext, lesson: api.Lesson) -> None:
    """Предлагает разобрать то, что лежало в разделе до нового урока."""
    await state.set_state(Sort.offer)
    await state.update_data(units=lesson.units, available=lesson.themes)
    await bot.send_message(
        chat,
        texts.LEFTOVER.format(left=len(lesson.units)),
        reply_markup=keyboards.sort(),
    )


@router.callback_query(Sort.offer, F.data == keyboards.SORT_LATER)
async def handle_later(callback: CallbackQuery, state: FSMContext) -> None:
    """Оставляет раздел как есть: разбор предложится при следующем добавлении."""
    await state.clear()
    await callback.answer()
    await callback.bot.send_message(callback.from_user.id, texts.LATER)


@router.callback_query(Sort.offer, F.data == keyboards.SORT_GO)
async def handle_go(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает разбор: единицы идут по одной, темы галочками."""
    data = await state.get_data()

    await state.set_state(Sort.walk)
    await state.update_data(picked=[], total=len(data["units"]), done=0, themeless=0, card=0)
    await callback.answer()
    await callback.bot.send_message(callback.from_user.id, texts.LESSON)
    await _show(callback.bot, callback.from_user.id, state)


async def _show(bot: Bot, chat: int, state: FSMContext) -> None:
    """Показывает первую единицу очереди с темами галочками."""
    data = await state.get_data()
    units: list[api.Unit] = data["units"]

    if not units:
        await _finish(bot, chat, state)
        return

    sent = await bot.send_message(
        chat,
        texts.UNIT.format(
            position=data["done"] + 1, total=data["total"], title=escape(units[0].title)
        ),
        reply_markup=keyboards.themes(data["available"], []),
    )
    # Номер сообщения нужен, чтобы галочки правились в нём же, а не плодили новые.
    await state.update_data(card=sent.message_id)


async def _finish(bot: Bot, chat: int, state: FSMContext) -> None:
    """Отчитывается за разбор и забывает его."""
    data = await state.get_data()

    report = [texts.SORTED.format(done=data["done"])]
    if data["themeless"]:
        report.append(texts.THEMELESS.format(themeless=data["themeless"]))

    logger.info("разобрано единиц: %s, из них без темы: %s", data["done"], data["themeless"])
    await state.clear()
    await bot.send_message(chat, "\n".join(report))


@router.callback_query(Sort.walk, F.data.startswith(keyboards.SORT_THEME))
async def handle_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    """Ставит и снимает галочку на теме."""
    slug = (callback.data or "").removeprefix(keyboards.SORT_THEME)
    data = await state.get_data()
    picked: list[str] = data["picked"]

    picked = [item for item in picked if item != slug] if slug in picked else [*picked, slug]

    await state.update_data(picked=picked)
    await callback.answer()
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=data["card"],
        reply_markup=keyboards.themes(data["available"], picked),
    )


@router.callback_query(Sort.walk, F.data.in_({keyboards.SORT_DONE, keyboards.SORT_NONE}))
async def handle_apply(callback: CallbackQuery, state: FSMContext) -> None:
    """Выносит единицу из раздела — в отмеченные темы или ни в какие."""
    data = await state.get_data()
    unit: api.Unit = data["units"][0]
    # «Оставить без темы» — то же, что «Готово» ни с чем: выйти из раздела и ждать
    # темы, которую владелец создаст руками.
    picked: list[str] = [] if callback.data == keyboards.SORT_NONE else data["picked"]

    await callback.answer()

    try:
        await api.move(kind=unit.kind, unit=unit.id, themes=picked)
    except (api.BackendError, api.Occupied) as error:
        logger.warning("разбор оборвался после %s единиц: %s", data["done"], error)
        await state.clear()
        await callback.bot.send_message(
            callback.from_user.id,
            texts.SORT_BROKEN.format(reason=escape(str(error)), done=data["done"]),
        )
        return

    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id, message_id=data["card"], reply_markup=None
    )
    await state.update_data(
        units=data["units"][1:],
        picked=[],
        done=data["done"] + 1,
        themeless=data["themeless"] + (0 if picked else 1),
    )
    await _show(callback.bot, callback.from_user.id, state)
