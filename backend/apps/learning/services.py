"""Прогресс: чтение и запись состояний карточек."""

from datetime import datetime

from django.conf import settings
from django.db.models import F, Max, Q, QuerySet
from django.utils import timezone

from apps.common.models import Learner
from apps.learning.constants import LEARNING, REMINDER_STEP
from apps.learning.models import CardState
from apps.learning.queryset import AnyCard, link
from apps.learning.rules import State, next_state
from apps.learning.utils import enabled, is_awake


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


def waiting() -> QuerySet[Learner]:
    """Кому вообще шлём: свой чат, включённая логика и не выключенные напоминания."""
    people = Learner.objects.filter(reminders_on=True, telegram_id__isnull=False)

    if settings.SCHEDULING_FOR_ALL:
        return people

    return people.filter(scheduling=True)


def take_reminders(*, now: datetime | None = None) -> list[CardState]:
    """Карточки для чата: по одной на человека. Помечает отправку, чтобы шли по кругу."""
    now = now or timezone.now()

    if not is_awake(now):
        return []

    taken = []

    for learner in waiting().iterator():
        if not enabled(learner):
            continue

        last = states(learner).aggregate(at=Max("reminded_at"))["at"]

        # Шаг считается от последней отправки, а не от часов: тогда лишний вызов ручки
        # не превращается во второе сообщение.
        if last is not None and now - last < REMINDER_STEP:
            continue

        card = (
            states(learner)
            .filter(level=LEARNING)
            .filter(Q(form__isnull=False) | Q(phrase__isnull=False))
            .select_related("form", "phrase")
            .order_by(F("reminded_at").asc(nulls_first=True), "due_at")
            .first()
        )

        if card is None:
            continue

        # Первое сообщение идёт со вступлением, поэтому бот должен знать, оно ли это.
        card.is_first = last is None
        card.reminded_at = now
        card.save(update_fields=["reminded_at"])
        taken.append(card)

    return taken
