"""Выбор карточек для чата: кому, что и как часто."""

from datetime import datetime, timedelta

import pytest
from django.test import override_settings
from django.utils.timezone import make_aware

from apps.common.models import Learner
from apps.learning.constants import LEARNING
from apps.learning.models import CardState
from apps.learning.services import apply, take_reminders

# Полдень по Москве — внутри окна; часы в настройках проекта московские.
NOON = make_aware(datetime(2026, 8, 17, 12, 0))
NIGHT = make_aware(datetime(2026, 8, 17, 3, 0))

settings = override_settings(
    LADDER=[1, 2, 3, 4, 5], JITTER_PERCENT=0, FIRST_SIGHT_LEVEL=3, SIDES_NEEDED=2
)


@pytest.fixture
def student(db) -> Learner:
    """Человек, которому включили логику и не выключали напоминания."""
    return Learner.objects.create(telegram_id=555, username="ali", scheduling=True)


@pytest.mark.django_db
class TestTakeReminders:
    """Выбор карточек для чата: кому, какие, в каком порядке и как часто."""

    @settings
    def test_learning_card_goes_to_chat(self, student, form):
        """В чат идут только те слова, что не даются."""
        apply(learner=student, card=form, knows=False, now=NOON)

        taken = take_reminders(now=NOON)

        assert [card.card for card in taken] == [form]
        assert taken[0].reminded_at == NOON

    @settings
    def test_scheduled_card_stays_out(self, student, form):
        """Знакомое слово в чат не присылается: оно и так вернётся по сроку."""
        apply(learner=student, card=form, knows=True, now=NOON)
        apply(learner=student, card=form, knows=True, now=NOON + timedelta(minutes=1))

        assert take_reminders(now=NOON) == []

    @settings
    def test_card_waiting_for_its_other_side_stays_out(self, student, form):
        """Слово с одной верной стороной в чат не идёт: оно не забывалось, а недоспрошено."""
        apply(learner=student, card=form, knows=True, now=NOON)

        assert take_reminders(now=NOON) == []

    @settings
    def test_step_holds_the_next_message(self, student, form, phrase):
        """Второй вызов ручки подряд второго сообщения не даёт."""
        apply(learner=student, card=form, knows=False, now=NOON)
        apply(learner=student, card=phrase, knows=False, now=NOON)

        assert len(take_reminders(now=NOON)) == 1
        assert take_reminders(now=NOON + timedelta(minutes=59)) == []
        assert len(take_reminders(now=NOON + timedelta(minutes=61))) == 1

    @settings
    def test_unsent_first_then_the_oldest(self, student, form, phrase):
        """Слова идут по кругу: сначала неотправленные, потом те, что отправляли раньше всех."""
        apply(learner=student, card=form, knows=False, now=NOON)
        apply(learner=student, card=phrase, knows=False, now=NOON)

        first = take_reminders(now=NOON)[0]
        second = take_reminders(now=NOON + timedelta(hours=2))[0]

        third = take_reminders(now=NOON + timedelta(hours=4))[0]

        assert first.pk != second.pk
        assert third.pk == first.pk

    @settings
    def test_night_is_quiet(self, student, form):
        """Вне окна бот молчит, и отправка не помечается."""
        apply(learner=student, card=form, knows=False, now=NIGHT)

        assert take_reminders(now=NIGHT) == []
        assert CardState.objects.get().reminded_at is None

    @settings
    def test_switched_off_gets_nothing(self, student, form):
        """Выключил напоминания — не приходят."""
        apply(learner=student, card=form, knows=False, now=NOON)
        Learner.objects.update(reminders_on=False)

        assert take_reminders(now=NOON) == []

    @settings
    def test_without_the_checkbox_gets_nothing(self, form):
        """Без включённой логики напоминаний нет: прогресса у человека тоже нет."""
        stranger = Learner.objects.create(telegram_id=777)
        apply(learner=stranger, card=form, knows=False, now=NOON)

        assert take_reminders(now=NOON) == []

    @override_settings(
        SCHEDULING_FOR_ALL=True, LADDER=[1, 2], JITTER_PERCENT=0, FIRST_SIGHT_LEVEL=1
    )
    def test_open_to_all_needs_no_checkbox(self, form):
        """Когда логика открыта всем, галочка на напоминания больше не влияет."""
        stranger = Learner.objects.create(telegram_id=888)
        apply(learner=stranger, card=form, knows=False, now=NOON)

        assert len(take_reminders(now=NOON)) == 1

    @settings
    def test_each_learner_gets_one_card(self, student, form, phrase):
        """На человека — одна карточка за раз, зато каждому своя."""
        other = Learner.objects.create(telegram_id=999, scheduling=True)
        apply(learner=student, card=form, knows=False, now=NOON)
        apply(learner=other, card=phrase, knows=False, now=NOON)

        taken = take_reminders(now=NOON)

        assert len(taken) == 2
        assert {card.learner_id for card in taken} == {student.pk, other.pk}

    @settings
    def test_learner_without_progress_is_skipped(self, student):
        """Нечего напоминать — человек пропускается, а не получает пустое сообщение."""
        assert take_reminders(now=NOON) == []

    @settings
    def test_only_own_cards(self, student, form):
        """Чужие слова в чужой чат не уходят."""
        other = Learner.objects.create(telegram_id=1010, scheduling=True)
        apply(learner=other, card=form, knows=False, now=NOON)

        taken = take_reminders(now=NOON)

        assert [card.learner_id for card in taken] == [other.pk]
        assert CardState.objects.filter(learner=student).count() == 0
        assert taken[0].level == LEARNING
