"""Слово в группу: когда уезжает и в каком порядке идёт колода."""

from datetime import datetime, timedelta

import pytest
from django.test import override_settings
from django.utils.timezone import make_aware

from apps.learning import utils
from apps.learning.models import GroupPost
from apps.learning.services import take_group_card
from apps.learning.utils import group_slot
from apps.vocabulary.models import Word, WordForm

GROUP = override_settings(GROUP_CHAT_ID=-1001)

MORNING = make_aware(datetime(2026, 8, 17, 10, 4))
MIDDAY = make_aware(datetime(2026, 8, 17, 13, 0))
EVENING = make_aware(datetime(2026, 8, 17, 18, 30))
NIGHT = make_aware(datetime(2026, 8, 17, 3, 0))
NEXT_MORNING = make_aware(datetime(2026, 8, 18, 10, 1))


def add_word(arabic: str, translation: str) -> WordForm:
    """Ещё одна форма в колоде: у каждой своё слово, разбирать числа тут нечего."""
    word = Word.objects.create(themes=["nouns"])

    return WordForm.objects.create(word=word, number=1, arabic=arabic, translation_ru=translation)


@pytest.fixture(autouse=True)
def hours(monkeypatch):
    """Часы слотов задаёт тест: читая ту же константу, он подтвердил бы любую."""
    monkeypatch.setattr(utils, "GROUP_HOURS", (10, 18))


@pytest.fixture
def deck(db) -> list[WordForm]:
    """Колода из двух слов."""
    return [add_word("كِتَاب", "книга"), add_word("بَاب", "дверь")]


class TestGroupSlot:
    """Слот рассылки: час, который уже наступил, и часы берутся из константы."""

    def test_slot_starts_at_its_hour(self):
        """Слот — час, который уже наступил, а не «прошло столько-то от прошлого раза»."""
        assert group_slot(MORNING) == MORNING.replace(hour=10, minute=0)
        assert group_slot(MIDDAY) == MIDDAY.replace(hour=10, minute=0)
        assert group_slot(EVENING) == EVENING.replace(hour=18, minute=0)

    def test_before_the_first_slot_there_is_none(self):
        """До первого часа слота нет: ночью в группу не пишем."""
        assert group_slot(NIGHT) is None

    def test_slots_are_read_from_the_constant(self, monkeypatch):
        """Часы берутся из константы, а не зашиты в разбор: с тремя слотами их три."""
        monkeypatch.setattr(utils, "GROUP_HOURS", (9, 13, 17))

        assert group_slot(MIDDAY) == MIDDAY.replace(hour=13, minute=0)
        assert group_slot(MORNING) == MORNING.replace(hour=9, minute=0)


@pytest.mark.django_db
class TestTakeGroupCard:
    """Слово для группы: когда уезжает, в каком порядке идёт колода и что помечается."""

    @GROUP
    def test_one_word_per_slot(self, deck):
        """За слот уезжает ровно одно слово, сколько бы раз бот ни спросил."""
        assert take_group_card(now=MORNING) is not None
        assert take_group_card(now=MIDDAY) is None
        assert take_group_card(now=EVENING) is not None

    @GROUP
    def test_night_is_quiet(self, deck):
        """Ночью не отправляем и карточку не помечаем."""
        assert take_group_card(now=NIGHT) is None
        assert GroupPost.objects.count() == 0

    @GROUP
    def test_deck_goes_around_without_repeats(self, deck):
        """Слово не повторяется, пока не пройдёт вся колода."""
        first = take_group_card(now=MORNING)
        second = take_group_card(now=EVENING)

        assert {first, second} == set(deck)

    @GROUP
    def test_new_circle_starts_with_the_oldest(self, deck):
        """Колода кончилась — круг начинается заново, с самого давнего слова."""
        first = take_group_card(now=MORNING)
        take_group_card(now=EVENING)

        assert take_group_card(now=NEXT_MORNING) == first

    @GROUP
    def test_a_new_word_jumps_the_queue(self, deck):
        """Добавленное слово уезжает раньше второго круга: неотправленные идут первыми."""
        take_group_card(now=MORNING)
        take_group_card(now=EVENING)
        added = add_word("قَلَم", "ручка")

        assert take_group_card(now=NEXT_MORNING) == added

    @GROUP
    def test_phrases_stay_out(self, phrase):
        """Фразы в группу не шлём: там только слова."""
        assert take_group_card(now=MORNING) is None
        assert GroupPost.objects.count() == 0

    @override_settings(GROUP_CHAT_ID=0)
    def test_without_a_group_nothing_is_spent(self, deck):
        """Группа не задана — колода не тратится: иначе слова помечались бы впустую."""
        assert take_group_card(now=MORNING) is None
        assert take_group_card(now=MORNING, forced=True) is None
        assert GroupPost.objects.count() == 0

    @GROUP
    def test_empty_deck_sends_nothing(self):
        """Пустая колода — молчание, а не пустое сообщение."""
        assert take_group_card(now=MORNING) is None

    @GROUP
    def test_deleted_word_takes_its_row(self, deck):
        """Удалённая карточка уносит запись об отправке: чистит база, а не мы."""
        card = take_group_card(now=MORNING)
        card.delete()

        assert GroupPost.objects.count() == 0

    @GROUP
    def test_the_sent_word_is_the_one_marked(self, deck):
        """Помечается ровно та карточка, что уехала, и временем отправки."""
        card = take_group_card(now=MORNING)
        post = GroupPost.objects.get()

        assert post.card == card
        assert post.sent_at == MORNING

    @GROUP
    def test_the_circle_moves_the_same_row(self, deck):
        """На втором круге строка не заводится заново, а двигается: их столько же, сколько слов."""
        take_group_card(now=MORNING)
        take_group_card(now=EVENING)
        take_group_card(now=NEXT_MORNING)

        assert GroupPost.objects.count() == len(deck)
        assert GroupPost.objects.order_by("-sent_at").first().sent_at == NEXT_MORNING

    @GROUP
    def test_a_late_ask_still_sends(self, deck):
        """Бот спросил через час после часа слота — слово всё равно уезжает."""
        assert take_group_card(now=MORNING + timedelta(hours=2)) is not None

    @GROUP
    def test_forced_ignores_the_schedule(self, deck):
        """Разовая отправка не смотрит на слот: ночью тоже уедет."""
        assert take_group_card(now=NIGHT, forced=True) is not None

    @GROUP
    def test_forced_moves_the_circle(self, deck):
        """Отправленное вручную слово помечается, иначе оно вернулось бы вторым заходом."""
        card = take_group_card(now=NIGHT, forced=True)

        assert take_group_card(now=MORNING) != card
