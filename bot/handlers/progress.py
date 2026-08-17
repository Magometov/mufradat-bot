import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, User

from bot import api, keyboards, texts
from bot.plural import CARDS, plural

logger = logging.getLogger(__name__)

router = Router()


def _who(source: Message | CallbackQuery) -> User | None:
    """Кто прислал. Подписи у апдейта нет — бэкенду доверять id можно только по секрету."""
    return source.from_user


async def _state(user: User) -> api.Progress | None:
    """Сводка по человеку. `None` — бэкенд не ответил, и говорить об этом человеку нечего."""
    try:
        return await api.progress(telegram_id=user.id, username=user.username or "")
    except api.BackendError as error:
        logger.warning("сводка не пришла: %s", error)

        return None


def _reminders_text(state: api.Progress) -> str:
    """Что сказать про напоминания: без прогресса включать их бессмысленно."""
    if state.cards == 0:
        return texts.REMINDERS_NO_PROGRESS

    return texts.REMINDERS_ON if state.reminders_on else texts.REMINDERS_OFF


@router.message(Command("reminders"))
async def handle_reminders(message: Message) -> None:
    """Показывает состояние напоминаний и даёт его переключить."""
    user = _who(message)

    if user is None:
        return

    state = await _state(user)

    if state is None:
        await message.answer(texts.BACKEND_SILENT)

        return

    keyboard = keyboards.reminders(state.reminders_on) if state.cards else None

    await message.answer(_reminders_text(state), reply_markup=keyboard)


@router.callback_query(F.data == keyboards.REMINDERS_SWITCH)
async def handle_switch(call: CallbackQuery) -> None:
    """Переключает напоминания и правит то же сообщение: чат не засоряется."""
    user = _who(call)

    if user is None or call.message is None:
        return

    try:
        state = await api.switch_reminders(telegram_id=user.id, username=user.username or "")
    except api.BackendError as error:
        logger.warning("напоминания не переключились: %s", error)
        await call.answer("Бэкенд не ответил, попробуй ещё раз")

        return

    await call.message.edit_text(
        _reminders_text(state),
        reply_markup=keyboards.reminders(state.reminders_on),
    )
    await call.answer()


@router.message(Command("reset"))
async def handle_reset(message: Message) -> None:
    """Спрашивает подтверждение: сброс необратим, и число карточек надо видеть заранее."""
    user = _who(message)

    if user is None:
        return

    state = await _state(user)

    if state is None:
        await message.answer(texts.BACKEND_SILENT)

        return

    if state.cards == 0:
        await message.answer(texts.RESET_EMPTY)

        return

    await message.answer(
        texts.RESET_ASK.format(cards=state.cards, cards_word=plural(state.cards, CARDS)),
        reply_markup=keyboards.reset(),
    )


@router.callback_query(F.data == keyboards.RESET_GO)
async def handle_reset_go(call: CallbackQuery) -> None:
    """Обнуляет прогресс. Колода остаётся: уходят только уровни и сроки."""
    user = _who(call)

    if user is None or call.message is None:
        return

    try:
        await api.reset_progress(telegram_id=user.id, username=user.username or "")
    except api.BackendError as error:
        logger.warning("прогресс не сброшен: %s", error)
        await call.answer("Бэкенд не ответил, попробуй ещё раз")

        return

    logger.info("прогресс сброшен по просьбе %s", user.id)
    await call.message.edit_text(texts.RESET_DONE)
    await call.answer()


@router.callback_query(F.data == keyboards.RESET_KEEP)
async def handle_reset_keep(call: CallbackQuery) -> None:
    """Отказ от сброса."""
    if call.message is None:
        return

    await call.message.edit_text(texts.RESET_KEPT)
    await call.answer()


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Выжимка про расписание и кнопка в подсказки приложения."""
    await message.answer(texts.HELP, reply_markup=keyboards.tips())
