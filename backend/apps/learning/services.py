"""Прогресс: чтение и запись состояний карточек."""

from datetime import datetime

from django.db.models import QuerySet
from django.utils import timezone

from apps.common.models import Learner
from apps.learning.models import CardState
from apps.learning.queryset import AnyCard, link
from apps.learning.rules import State, next_state


def states(learner: Learner) -> QuerySet[CardState]:
    """Всё, что человек уже видел."""
    return CardState.objects.filter(learner=learner)


def apply(
    *,
    learner: Learner,
    card: AnyCard,
    knows: bool,
    now: datetime | None = None,
) -> CardState:
    """Записывает оценку: считает новый уровень и срок по правилам."""
    now = now or timezone.now()
    state = CardState.objects.filter(learner=learner).for_card(card).first()
    current = State(level=state.level, step=state.step) if state is not None else None
    fresh, due_at = next_state(current, knows=knows, now=now)

    if state is None:
        return CardState.objects.create(
            learner=learner,
            level=fresh.level,
            step=fresh.step,
            due_at=due_at,
            answered_at=now,
            **link(card),
        )

    state.level = fresh.level
    state.step = fresh.step
    state.due_at = due_at
    state.answered_at = now
    state.save(update_fields=["level", "step", "due_at", "answered_at"])

    return state
