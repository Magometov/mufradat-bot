"""Прогресс: чтение и запись состояний карточек."""

from datetime import datetime

from django.db.models import QuerySet
from django.utils import timezone

from apps.common.models import Learner
from apps.learning.models import CardState
from apps.learning.queryset import AnyCard, link
from apps.learning.rules import State, next_state
from apps.learning.utils import enabled


def states(learner: Learner) -> QuerySet[CardState]:
    """Всё, что человек уже видел."""
    return CardState.objects.filter(learner=learner)


def count_states(learner: Learner) -> int:
    """Сколько карточек человек уже оценивал."""
    return states(learner).count()


def summary(learner: Learner) -> dict:
    """Сводка по человеку: ею бот отвечает на команды."""
    return {
        "reminders_on": learner.reminders_on,
        "scheduling": enabled(learner),
        "cards": count_states(learner),
    }


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

    # Оценка не новее записанной — эту пачку уже применяли: повтор уровень не двигает.
    if state is not None and state.answered_at is not None and now <= state.answered_at:
        return state

    fresh, due_at = next_state(_current(state), knows=knows, now=now)
    fields = {
        "level": fresh.level,
        "step": fresh.step,
        "lapses": fresh.lapses,
        "lapsed_from": fresh.lapsed_from,
        "due_at": due_at,
        "answered_at": now,
    }

    if state is None:
        return CardState.objects.create(learner=learner, **fields, **link(card))

    for name, value in fields.items():
        setattr(state, name, value)

    state.save(update_fields=list(fields))

    return state


def _current(state: CardState | None) -> State | None:
    """Состояние карточки, каким его видят правила. `None` — карточку видят впервые."""
    if state is None:
        return None

    return State(
        level=state.level,
        step=state.step,
        lapses=state.lapses,
        lapsed_from=state.lapsed_from,
    )


def reset_progress(learner: Learner) -> int:
    """Обнуляет прогресс и отдаёт, сколько карточек забыто. Колоду не трогает."""
    cleared, _ = states(learner).delete()

    return cleared
