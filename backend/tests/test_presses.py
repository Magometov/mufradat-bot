"""Времена нажатий в пачке: часам клиента верим ровно настолько, насколько можно."""

from datetime import UTC, datetime, timedelta

import pytest

from apps.learning.utils import presses

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)


class TestPresses:
    """Пачка оценок приходит со своими временами: где-то верными, где-то из будущего."""

    def test_empty_batch_stays_empty(self):
        """Пустой пачке нечего засчитывать."""

        assert presses([], NOW) == []

    @pytest.mark.parametrize(
        "times",
        [
            [NOW - timedelta(minutes=5)],
            [NOW - timedelta(minutes=5), NOW - timedelta(minutes=1)],
            [NOW],
        ],
        ids=["одно нажатие", "несколько подряд", "ровно сейчас"],
    )
    def test_honest_clock_is_left_alone(self, times):
        """Часы не убежали — времена засчитываются как есть."""

        assert presses(times, NOW) == times

    def test_future_batch_is_moved_back_whole(self):
        """Пачка с убежавших вперёд часов сдвигается целиком: последнее нажатие — сейчас."""
        ahead = timedelta(minutes=30)
        times = [NOW + ahead - timedelta(seconds=20), NOW + ahead]

        assert presses(times, NOW) == [NOW - timedelta(seconds=20), NOW]

    def test_gaps_between_presses_survive_the_move(self):
        """Промежутки между нажатиями остаются: по ним сервер и отличает стороны карточки.

        Обрезка каждого времени по отдельности слепила бы их в одно, и вторая сторона
        карточки в той же пачке сошла бы за повтор первой.
        """
        times = [NOW + timedelta(hours=1), NOW + timedelta(hours=1, seconds=20)]

        moved = presses(times, NOW)

        assert moved[1] - moved[0] == timedelta(seconds=20)
        assert len(set(moved)) == 2

    def test_late_answers_move_with_the_batch(self):
        """Сдвиг общий на пачку: старое нажатие рядом с будущим уезжает вместе с ним."""
        times = [NOW - timedelta(days=1), NOW + timedelta(minutes=10)]

        assert presses(times, NOW) == [NOW - timedelta(days=1, minutes=10), NOW]
