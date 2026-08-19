"""Лестница сроков: что делает оценка с уровнем и сроком."""

from datetime import UTC, datetime, timedelta

import pytest
from django.test import override_settings

from apps.learning.rules import State, next_state

NOW = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
# Лестница задана здесь, а не взята из окружения: тест на её значениях и стоит.
# Читается ли она из настроек, проверяет отдельный тест с другой лестницей.
LADDER = [1, 3, 7, 16, 35]

settings = override_settings(
    LADDER=LADDER, JITTER_PERCENT=10, FIRST_SIGHT_LEVEL=3, LAPSE_DROP=2, SIDES_NEEDED=2
)


def days_between(due: datetime, now: datetime = NOW) -> float:
    """Сколько дней между сроком и отсчётом: в днях ожидания читаются проще."""
    return (due - now) / timedelta(days=1)


class TestNextState:
    """Правило расписания: уровень, счёт верных, след промахов и срок после оценки."""

    @settings
    @pytest.mark.parametrize(
        "current",
        [None, State(level=3), State(level=0, step=0, lapses=1, lapsed_from=5)],
        ids=["новая", "знакомая", "в изучении"],
    )
    def test_first_correct_side_only_counts(self, current):
        """Верная сторона срок не двигает на любой ступени: нужна и вторая."""
        state, due = next_state(current, knows=True, now=NOW)

        assert state.step == 1
        assert due == NOW

    @settings
    def test_both_sides_of_a_new_card_go_far(self):
        """Обе стороны с первого взгляда — знал заранее: сразу третий уровень, неделя."""
        first, _ = next_state(None, knows=True, now=NOW)
        state, due = next_state(first, knows=True, now=NOW)

        assert state == State(level=3, step=0)
        assert days_between(due) == pytest.approx(7, rel=0.1)

    @settings
    def test_unknown_new_card_goes_to_learning(self):
        """Новая и не вспомнилась — в изучение со сроком «сейчас». Падать ей не с чего."""
        state, due = next_state(None, knows=False, now=NOW)

        assert state == State(level=0, step=0, lapses=1, lapsed_from=0)
        assert due == NOW

    @settings
    def test_second_correct_closes_learning(self):
        """Вторая верная сторона закрывает изучение — на завтра."""
        state, due = next_state(State(level=0, step=1, lapses=1), knows=True, now=NOW)

        assert state == State(level=1, step=0, lapses=1)
        assert days_between(due) == pytest.approx(1, rel=0.1)

    @settings
    @pytest.mark.parametrize(
        ("lapsed_from", "level", "days"),
        [(5, 3, 7), (3, 1, 1), (2, 1, 1)],
        ids=["с пятой на третью", "с третьей на первую", "ниже первой некуда"],
    )
    def test_relearned_card_returns_below_the_step_it_fell_from(self, lapsed_from, level, days):
        """Переученная карточка встаёт ниже прежней ступени, но не ниже первой."""
        current = State(level=0, step=1, lapses=1, lapsed_from=lapsed_from)

        state, due = next_state(current, knows=True, now=NOW)

        assert state == State(level=level, lapses=1)
        assert days_between(due) == pytest.approx(days, rel=0.1)

    @settings
    def test_miss_remembers_the_step_it_fell_from(self):
        """Промах помнит ступень падения и считает себя в счёте промахов."""
        state, _ = next_state(State(level=4, step=1, lapses=1), knows=False, now=NOW)

        assert state == State(level=0, step=0, lapses=2, lapsed_from=4)

    @settings
    def test_miss_in_learning_keeps_the_old_fall(self):
        """Промах в изучении прежнее падение не стирает: возвращаться на ту же ступень."""
        current = State(level=0, step=1, lapses=2, lapsed_from=5)

        state, _ = next_state(current, knows=False, now=NOW)

        assert state == State(level=0, step=0, lapses=3, lapsed_from=5)

    @settings
    def test_miss_in_learning_resets_the_count_of_correct_answers(self):
        """Промах в изучении обнуляет счёт верных, а промахи считает дальше."""
        state, due = next_state(State(level=0, step=1, lapses=1), knows=False, now=NOW)

        assert state == State(level=0, step=0, lapses=2)
        assert due == NOW

    @settings
    def test_known_card_climbs_one_step(self):
        """Знакомая карточка поднимается на уровень, не забывая счёт промахов."""
        state, due = next_state(State(level=3, step=1, lapses=2), knows=True, now=NOW)

        assert state == State(level=4, step=0, lapses=2)
        assert days_between(due) == pytest.approx(16, rel=0.1)

    @settings
    def test_top_level_stays_on_top(self):
        """С последнего уровня подниматься некуда."""
        state, due = next_state(State(level=len(LADDER), step=1), knows=True, now=NOW)

        assert state == State(level=len(LADDER), step=0)
        assert days_between(due) == pytest.approx(35, rel=0.1)

    @settings
    def test_forgotten_card_falls_to_learning(self):
        """Забытая карточка падает в изучение с любого уровня."""
        state, due = next_state(State(level=5), knows=False, now=NOW)

        assert state == State(level=0, step=0, lapses=1, lapsed_from=5)
        assert due == NOW

    @settings
    def test_intervals_are_spread(self):
        """Разброс работает и держится в пределах: одинаковых сроков подряд не бывает."""
        spans = {
            days_between(next_state(State(level=3, step=1), knows=True, now=NOW)[1])
            for _ in range(20)
        }

        assert len(spans) > 1
        assert all(14.4 <= span <= 17.6 for span in spans)


class TestRulesFromSettings:
    """Числа расписания приходят из настроек, а не зашиты в правило."""

    @override_settings(LADDER=[2, 9], JITTER_PERCENT=0, FIRST_SIGHT_LEVEL=1, SIDES_NEEDED=1)
    def test_ladder_and_first_sight_come_from_settings(self):
        """Лестница и уровень первого взгляда берутся из настроек."""
        first, due = next_state(None, knows=True, now=NOW)

        assert first == State(level=1)
        assert days_between(due) == 2

        second, due = next_state(first, knows=True, now=NOW)

        assert second == State(level=2)
        assert days_between(due) == 9

    @override_settings(LADDER=LADDER, JITTER_PERCENT=0, SIDES_NEEDED=3)
    def test_number_of_sides_comes_from_settings(self):
        """Сколько верных сторон закрывают карточку — настройка: с тремя нужен третий ответ."""
        second, _ = next_state(State(level=1, step=1), knows=True, now=NOW)
        third, due = next_state(second, knows=True, now=NOW)

        assert second == State(level=1, step=2)
        assert third == State(level=2)
        assert days_between(due) == 3

    @override_settings(LADDER=LADDER, JITTER_PERCENT=0, LAPSE_DROP=4, SIDES_NEEDED=2)
    def test_lapse_drop_comes_from_settings(self):
        """На сколько ступеней опускать забытую — настройка: с четырьмя падение глубже."""
        state, _ = next_state(State(level=0, step=1, lapses=1, lapsed_from=5), knows=True, now=NOW)

        assert state == State(level=1, lapses=1)

    @override_settings(LADDER=[1, 3, 7], JITTER_PERCENT=0, FIRST_SIGHT_LEVEL=9, SIDES_NEEDED=2)
    def test_first_sight_level_above_the_ladder_stops_at_its_top(self):
        """Ступень выше лестницы — опечатка в настройках, а не повод уронить ручку."""
        state, due = next_state(State(level=0, step=1), knows=True, now=NOW)

        assert state == State(level=3)
        assert days_between(due) == 7

    @override_settings(LADDER=[1, 3], JITTER_PERCENT=0, LAPSE_DROP=2, SIDES_NEEDED=2)
    def test_levels_from_a_longer_ladder_fit_the_shorter_one(self):
        """Лестницу укоротили при уже расставленных уровнях: карточка встаёт на её верх."""
        current = State(level=0, step=1, lapses=1, lapsed_from=7)

        state, due = next_state(current, knows=True, now=NOW)

        assert state == State(level=2, lapses=1)
        assert days_between(due) == 3


class TestCardLife:
    """Жизнь карточки от первого показа до второго переучивания.

    Те же шаги проверяет `frontend/src/utils/predict.spec.ts`: правило живёт в двух
    местах, и разъехаться они должны с треском, а не тихо.
    """

    # Оценка за оценкой, а рядом — во что карточка после неё превращается и на сколько
    # дней уезжает. Ноль дней значит «срок сейчас»: карточка вернётся в этом же сеансе.
    LIFE = [
        (True, State(level=0, step=1), 0),
        (True, State(level=3), 7),
        (True, State(level=3, step=1), 0),
        (True, State(level=4), 16),
        (False, State(lapses=1, lapsed_from=4), 0),
        (True, State(step=1, lapses=1, lapsed_from=4), 0),
        (True, State(level=2, lapses=1), 3),
        (True, State(level=2, step=1, lapses=1), 0),
        (True, State(level=3, lapses=1), 7),
        (False, State(lapses=2, lapsed_from=3), 0),
        (False, State(lapses=3, lapsed_from=3), 0),
        (True, State(step=1, lapses=3, lapsed_from=3), 0),
        (True, State(level=1, lapses=3), 1),
    ]

    @override_settings(
        LADDER=LADDER, JITTER_PERCENT=0, FIRST_SIGHT_LEVEL=3, LAPSE_DROP=2, SIDES_NEEDED=2
    )
    def test_card_lives_the_life_the_app_predicts(self):
        """Каждый шаг жизни даёт тот же уровень, счёт, след падения и срок, что в приложении."""
        state = None

        for knows, expected, days in self.LIFE:
            state, due = next_state(state, knows=knows, now=NOW)

            assert (state, days_between(due)) == (expected, days)
