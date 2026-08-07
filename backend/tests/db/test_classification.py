import csv
from collections import Counter
from pathlib import Path

import pytest

from apps.vocabulary.classification import themes_for
from apps.vocabulary.themes import Theme

#: Выгрузка колоды с сервера: на ней правила и проверяются целиком.
#: В репозиторий она не едет, поэтому проверки по ней пропускаются, когда файла нет.
SNAPSHOT = Path(__file__).resolve().parents[3] / "docs" / "superpowers" / "words.csv"

needs_snapshot = pytest.mark.skipif(
    not SNAPSHOT.exists(),
    reason=f"нет выгрузки колоды: {SNAPSHOT}",
)


def test_single_noun_falls_through_to_nouns() -> None:
    assert themes_for("верблюд") == [Theme.NOUNS]


def test_idafa_of_two_nouns_is_nouns() -> None:
    """«Ключ от автомобиля» — идафа: «от» тут переводит связь, а не предлог."""
    assert themes_for("ключ от автомобиля") == [Theme.NOUNS]
    assert themes_for("школа для девочек") == [Theme.NOUNS]


def test_locative_phrase_is_a_preposition_drill() -> None:
    assert themes_for("книга на столе") == [Theme.QUESTIONS]
    assert themes_for("парта справа от двери") == [Theme.QUESTIONS]


def test_verb_wins_over_preposition() -> None:
    """В «мужчина идёт в мечеть» отрабатывается глагол, а не предлог «в»."""
    assert themes_for("мужчина идёт в мечеть") == [Theme.VERBS]


def test_question_keeps_its_theme_even_with_a_verb() -> None:
    assert themes_for("где живёт врач?") == [Theme.VERBS, Theme.QUESTIONS]


def test_card_gets_several_themes() -> None:
    assert themes_for("сколько братьев в твоей семье?") == [
        Theme.NUMBERS,
        Theme.FAMILY,
        Theme.QUESTIONS,
    ]
    assert themes_for("моя семья большая") == [Theme.FAMILY, Theme.ANTONYMS]


def test_grammar_note_in_brackets_is_ignored() -> None:
    """«три (муж. род)» — это цифра, а пометка в скобках не должна мешать."""
    assert themes_for("три (муж. род)") == [Theme.NUMBERS]
    assert themes_for("как тебя зовут? (к мужчине)") == [Theme.GREETINGS, Theme.QUESTIONS]


def test_family_stem_does_not_catch_the_numeral_seven() -> None:
    """«Семь» и «семья» начинаются одинаково — разводить их надо словом, не префиксом."""
    assert themes_for("семь домов") == [Theme.NUMBERS]
    assert themes_for("семья") == [Theme.FAMILY]


def test_country_and_nationality_go_to_greetings() -> None:
    assert themes_for("Египет") == [Theme.GREETINGS]
    assert themes_for("египтянка") == [Theme.GREETINGS]


def test_themes_come_in_button_order() -> None:
    """Порядок важен: он же уходит в API и определяет порядок кнопок."""
    themes = themes_for("сколько мальчиков в семье?")

    assert themes == sorted(themes, key=Theme.values.index)


@pytest.fixture(scope="module")
def snapshot() -> list[dict[str, str]]:
    with SNAPSHOT.open(encoding="utf-8") as file:
        return list(csv.DictReader(file))


@needs_snapshot
def test_snapshot_is_the_whole_deck(snapshot: list[dict[str, str]]) -> None:
    assert len(snapshot) == 986


@needs_snapshot
def test_every_card_of_the_deck_gets_a_theme(snapshot: list[dict[str, str]]) -> None:
    without = [row["translation_ru"] for row in snapshot if not themes_for(row["translation_ru"])]

    assert without == []


@needs_snapshot
def test_no_theme_swallows_the_deck(snapshot: list[dict[str, str]]) -> None:
    """Тема размером в полколоды бесполезна: по ней уже не «повторить только это»."""
    counts = Counter(theme for row in snapshot for theme in themes_for(row["translation_ru"]))

    assert counts.most_common(1)[0][1] < len(snapshot) / 2


@needs_snapshot
def test_every_theme_has_cards(snapshot: list[dict[str, str]]) -> None:
    counts = Counter(theme for row in snapshot for theme in themes_for(row["translation_ru"]))

    assert {slug: counts[slug] for slug in Theme.values if counts[slug] == 0} == {}
