"""Правила расписания: куда уезжает карточка после оценки."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from random import uniform

from django.conf import settings

from apps.learning.constants import FIRST_SCHEDULED, LEARNING


@dataclass(frozen=True)
class State:
    """Уровень лестницы, счёт подтверждённых сторон и след промахов."""

    level: int = LEARNING
    step: int = 0
    # Сколько раз слово забывалось за свою жизнь: по нему видны слова-паразиты.
    lapses: int = 0
    # Ступень, с которой карточка упала: на неё же и возвращается, только ниже.
    lapsed_from: int = 0


def interval(level: int) -> timedelta:
    """Срок уровня с разбросом: иначе раздел, пройденный за вечер, вернётся лавиной."""
    days = settings.LADDER[level - 1]
    spread = days * settings.JITTER_PERCENT / 100

    return timedelta(days=uniform(days - spread, days + spread))


def next_state(current: State | None, *, knows: bool, now: datetime) -> tuple[State, datetime]:
    """Состояние и срок показа после оценки. `None` — карточку видят впервые."""
    # Новая карточка — это состояние по умолчанию: дальше правило одно на всех.
    state = current if current is not None else State()

    if not knows:
        return _forgotten(state), now

    step = state.step + 1

    # Подтверждена не всякая сторона — карточка возвращается в этом же сеансе за остальными.
    if step < settings.SIDES_NEEDED:
        return replace(state, step=step), now

    level = _closed_level(state)

    return State(level=level, lapses=state.lapses), now + interval(level)


def _forgotten(state: State) -> State:
    """Изучение с начала, но со следом падения: промах в изучении прежний след не стирает."""
    fell_from = state.lapsed_from if state.level == LEARNING else state.level

    return State(lapses=state.lapses + 1, lapsed_from=fell_from)


def _closed_level(state: State) -> int:
    """На какую ступень встаёт карточка, подтвердившая все стороны."""
    if state.level != LEARNING:
        return min(state.level + 1, len(settings.LADDER))

    # Ни разу не забывалась — знал заранее, а не вспомнил с третьего раза.
    if state.lapses == 0:
        return settings.FIRST_SIGHT_LEVEL

    # Переученная возвращается ниже прежней ступени, но не в самый низ.
    return max(FIRST_SCHEDULED, state.lapsed_from - settings.LAPSE_DROP)
