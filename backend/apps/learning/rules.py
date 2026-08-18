"""Правила расписания: куда уезжает карточка после оценки."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from random import uniform

from django.conf import settings

from apps.learning.constants import FIRST_SCHEDULED, LEARNING


@dataclass(frozen=True)
class State:
    """Уровень лестницы, счёт верных в изучении и след промахов."""

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
    if not knows:
        return _forgotten(current), now

    # Узнал с первого взгляда — знал заранее, а не вспомнил с третьего раза.
    if current is None:
        return State(level=settings.FIRST_SIGHT_LEVEL), now + interval(settings.FIRST_SIGHT_LEVEL)

    if current.level == LEARNING:
        if current.step < settings.LEARNING_NEEDED - 1:
            return replace(current, step=current.step + 1), now

        level = _relearned(current.lapsed_from)

        return State(level=level, lapses=current.lapses), now + interval(level)

    level = min(current.level + 1, len(settings.LADDER))

    return State(level=level, lapses=current.lapses), now + interval(level)


def _forgotten(current: State | None) -> State:
    """Изучение с начала, но со следом падения: промах в изучении прежний след не стирает."""
    if current is None:
        return State(lapses=1)

    fell_from = current.lapsed_from if current.level == LEARNING else current.level

    return State(lapses=current.lapses + 1, lapsed_from=fell_from)


def _relearned(lapsed_from: int) -> int:
    """Куда возвращается переученная карточка: ниже прежней ступени, но не в самый низ."""
    return max(FIRST_SCHEDULED, lapsed_from - settings.LAPSE_DROP)
