"""Запись прогресса: одна строка на пару «человек + карточка»."""

import pytest
from django.db import IntegrityError, transaction
from django.test import override_settings
from django.utils import timezone

from apps.common.models import Learner
from apps.learning import services
from apps.learning.models import CardState

# Сроки здесь не проверяются, поэтому лестница условная: важны только уровни и то, что
# без разброса даты предсказуемы.
settings = override_settings(LADDER=[1, 2, 3, 4, 5], JITTER_PERCENT=0, FIRST_SIGHT_LEVEL=3)


@settings
@pytest.mark.django_db
def test_first_answer_creates_the_state(learner, form):
    """Первая оценка заводит строку: до неё карточка «новая»."""
    state = services.apply(learner=learner, card=form, knows=True)

    assert state.level == 3
    assert state.form_id == form.pk
    assert state.phrase_id is None
    assert CardState.objects.count() == 1


@settings
@pytest.mark.django_db
def test_next_answers_update_the_same_row(learner, form):
    """Вторая оценка правит ту же строку, а не плодит новые."""
    services.apply(learner=learner, card=form, knows=True)
    state = services.apply(learner=learner, card=form, knows=True)

    assert state.level == 4
    assert CardState.objects.count() == 1


@settings
@pytest.mark.django_db
def test_forgetting_drops_to_learning(learner, form):
    """Забыл знакомое — карточка падает в изучение и ждёт «сейчас»."""
    services.apply(learner=learner, card=form, knows=True)
    state = services.apply(learner=learner, card=form, knows=False)

    assert (state.level, state.step) == (0, 0)
    assert state.due_at == state.answered_at


@settings
@pytest.mark.django_db
def test_phrase_and_form_use_their_own_links(learner, form, phrase):
    """У формы и фразы свои поля: номера в двух таблицах не сталкиваются."""
    services.apply(learner=learner, card=form, knows=True)
    services.apply(learner=learner, card=phrase, knows=False)

    assert CardState.objects.filter(form=form, phrase__isnull=True).count() == 1
    assert CardState.objects.filter(phrase=phrase, form__isnull=True).count() == 1


@settings
@pytest.mark.django_db
def test_deleting_card_takes_state_with_it(learner, form):
    """Удалили карточку — состояние уходит следом, сирот не остаётся."""
    services.apply(learner=learner, card=form, knows=True)

    form.delete()

    assert CardState.objects.count() == 0


@pytest.mark.django_db
def test_state_without_card_is_rejected(learner):
    """Состояние без карточки база не принимает."""
    with pytest.raises(IntegrityError), transaction.atomic():
        CardState.objects.create(learner=learner, due_at=timezone.now())


@settings
@pytest.mark.django_db
def test_states_belong_to_their_learner(learner, form, phrase):
    """Выборка отдаёт только своё: чужой прогресс не подмешивается."""
    stranger = Learner.objects.create(telegram_id=2002)
    services.apply(learner=learner, card=form, knows=True)
    services.apply(learner=stranger, card=phrase, knows=True)

    assert [state.card for state in services.states(learner)] == [form]
