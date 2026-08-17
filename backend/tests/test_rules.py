"""Лестница сроков: что делает оценка с уровнем и сроком."""

from datetime import UTC, datetime, timedelta

import pytest
from django.test import override_settings

from apps.learning.rules import State, next_state

NOW = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
# Лестница задана здесь, а не взята из окружения: тест на её значениях и стоит.
# Читается ли она из настроек, проверяет отдельный тест с другой лестницей.
LADDER = [1, 3, 7, 16, 35]

settings = override_settings(LADDER=LADDER, JITTER_PERCENT=10, FIRST_SIGHT_LEVEL=3)


def days_between(due, now=NOW) -> float:
    return (due - now) / timedelta(days=1)


@settings
def test_first_sight_goes_far():
    """Узнал с первого взгляда — знал заранее: сразу третий уровень, неделя."""
    state, due = next_state(None, knows=True, now=NOW)

    assert state == State(level=3, step=0)
    assert days_between(due) == pytest.approx(7, rel=0.1)


@settings
def test_unknown_new_card_goes_to_learning():
    """Новая и не вспомнилась — в изучение со сроком «сейчас»."""
    state, due = next_state(None, knows=False, now=NOW)

    assert state == State(level=0, step=0)
    assert due == NOW


@settings
def test_first_correct_in_learning_only_counts():
    """Первый верный в изучении срок не двигает: нужен второй подряд."""
    state, due = next_state(State(level=0, step=0), knows=True, now=NOW)

    assert state == State(level=0, step=1)
    assert due == NOW


@settings
def test_second_correct_closes_learning():
    """Второй верный подряд закрывает изучение — на завтра."""
    state, due = next_state(State(level=0, step=1), knows=True, now=NOW)

    assert state == State(level=1, step=0)
    assert days_between(due) == pytest.approx(1, rel=0.1)


@settings
def test_miss_in_learning_resets_the_count():
    """Промах в изучении обнуляет счёт верных."""
    state, due = next_state(State(level=0, step=1), knows=False, now=NOW)

    assert state == State(level=0, step=0)
    assert due == NOW


@settings
def test_known_card_climbs_one_step():
    """Знакомая карточка поднимается на один уровень."""
    state, due = next_state(State(level=3), knows=True, now=NOW)

    assert state == State(level=4, step=0)
    assert days_between(due) == pytest.approx(16, rel=0.1)


@settings
def test_top_level_stays_on_top():
    """С последнего уровня подниматься некуда."""
    state, due = next_state(State(level=len(LADDER)), knows=True, now=NOW)

    assert state == State(level=len(LADDER), step=0)
    assert days_between(due) == pytest.approx(35, rel=0.1)


@settings
def test_forgotten_card_falls_to_learning():
    """Забытая карточка падает в изучение с любого уровня."""
    state, due = next_state(State(level=5), knows=False, now=NOW)

    assert state == State(level=0, step=0)
    assert due == NOW


@settings
def test_intervals_are_spread():
    """Разброс работает и держится в пределах: одинаковых сроков подряд не бывает."""
    spans = {days_between(next_state(State(level=3), knows=True, now=NOW)[1]) for _ in range(20)}

    assert len(spans) > 1
    assert all(14.4 <= span <= 17.6 for span in spans)


@override_settings(LADDER=[2, 9], JITTER_PERCENT=0, FIRST_SIGHT_LEVEL=1)
def test_ladder_comes_from_settings():
    """Лестница и уровень первого взгляда берутся из настроек, а не из кода."""
    first, due = next_state(None, knows=True, now=NOW)
    assert first == State(level=1)
    assert days_between(due) == 2

    second, due = next_state(first, knows=True, now=NOW)
    assert second == State(level=2)
    assert days_between(due) == 9
