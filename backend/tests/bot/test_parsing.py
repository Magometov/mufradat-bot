import pytest

from apps.bot.parsing import ParseError, parse_entry


def test_arabic_first() -> None:
    parsed = parse_entry("بَيْت | дом")

    assert parsed.arabic == "بَيْت"
    assert parsed.translation_ru == "дом"
    assert parsed.transliteration == ""


def test_translation_first() -> None:
    """Порядок не важен: сторона определяется алфавитом, а не позицией."""
    parsed = parse_entry("дом | بَيْت")

    assert parsed.arabic == "بَيْت"
    assert parsed.translation_ru == "дом"


@pytest.mark.parametrize(
    "line",
    [
        "1. بَيْت | дом | bayt",
        "1) بَيْت | дом | bayt",
        "- بَيْت | дом | bayt",
        "• بَيْت | дом | bayt",
        "**بَيْت** | дом | bayt",
        "`بَيْت` | **дом** | bayt",
    ],
)
def test_ai_list_decoration_does_not_reach_the_card(line: str) -> None:
    """ИИ нумерует список и выделяет слова жирным. Без чистки «1.» и «**» вставали
    в колоду внутри арабского поля, и карточка молча показывала «1. بَيْت».
    """
    parsed = parse_entry(line)

    assert parsed.arabic == "بَيْت"
    assert parsed.translation_ru == "дом"


def test_dash_inside_translation_survives() -> None:
    """Чистится только маркер в начале строки, а не дефисы внутри перевода."""
    parsed = parse_entry("مَكْتَب | письменный стол — рабочий")

    assert parsed.translation_ru == "письменный стол — рабочий"


def test_transliteration_third() -> None:
    parsed = parse_entry("بَيْت | дом | bayt")

    assert parsed.transliteration == "bayt"


def test_transliteration_in_any_position() -> None:
    parsed = parse_entry("bayt | дом | بَيْت")

    assert parsed.arabic == "بَيْت"
    assert parsed.translation_ru == "дом"
    assert parsed.transliteration == "bayt"


def test_extra_spaces_are_trimmed() -> None:
    parsed = parse_entry("   بَيْت   |    дом   ")

    assert parsed.arabic == "بَيْت"
    assert parsed.translation_ru == "дом"


def test_translation_may_contain_latin() -> None:
    parsed = parse_entry("بَيْت | дом (house)")

    assert parsed.translation_ru == "дом (house)"
    assert parsed.transliteration == ""


def test_multiword_arabic_is_a_card_too() -> None:
    """Деления на слова и фразы нет: многословное арабское — такая же карточка."""
    parsed = parse_entry("مَا اسْمُكَ؟ | как тебя зовут? (к мужчине)")

    assert parsed.arabic == "مَا اسْمُكَ؟"
    assert parsed.translation_ru == "как тебя зовут? (к мужчине)"


def test_missing_separator() -> None:
    with pytest.raises(ParseError, match="две части"):
        parse_entry("بَيْت")


def test_missing_arabic() -> None:
    with pytest.raises(ParseError, match="арабск"):
        parse_entry("дом | house")


def test_missing_translation() -> None:
    with pytest.raises(ParseError, match="перевод"):
        parse_entry("بَيْت | كِتَاب")


def test_too_many_parts() -> None:
    with pytest.raises(ParseError, match="трёх"):
        parse_entry("بَيْت | дом | bayt | лишнее")
