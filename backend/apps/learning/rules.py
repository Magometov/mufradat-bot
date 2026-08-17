"""Правила расписания: куда уезжает карточка после оценки."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from random import uniform

from django.conf import settings

from apps.learning.constants import FIRST_SCHEDULED, LEARNING, NEEDED


@dataclass(frozen=True)
class State:
    """Уровень лестницы и сколько верных ответов подряд уже дано в изучении."""

    level: int = LEARNING
    step: int = 0


def interval(level: int) -> timedelta:
    """Срок уровня с разбросом: иначе раздел, пройденный за вечер, вернётся лавиной."""
    days = settings.LADDER[level - 1]
    spread = days * settings.JITTER_PERCENT / 100

    return timedelta(days=uniform(days - spread, days + spread))


def next_state(current: State | None, *, knows: bool, now: datetime) -> tuple[State, datetime]:
    """Состояние и срок показа после оценки. `None` — карточку видят впервые."""
    if not knows:
        return State(), now

    # Узнал с первого взгляда — знал заранее, а не вспомнил с третьего раза.
    if current is None:
        return State(level=settings.FIRST_SIGHT_LEVEL), now + interval(settings.FIRST_SIGHT_LEVEL)

    if current.level == LEARNING:
        if current.step < NEEDED - 1:
            return State(step=current.step + 1), now

        return State(level=FIRST_SCHEDULED), now + interval(FIRST_SCHEDULED)

    level = min(current.level + 1, len(settings.LADDER))

    return State(level=level), now + interval(level)
