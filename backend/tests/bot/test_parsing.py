import pytest

from apps.bot.parsing import ParseError, parse_entry
from apps.vocabulary.enums import Kind


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


def test_phrase_is_detected_by_spaces() -> None:
    parsed = parse_entry("مَا اسْمُكَ؟ | как тебя зовут? (к мужчине)")

    assert parsed.kind == Kind.PHRASE


def test_single_word_is_a_word() -> None:
    assert parse_entry("بَيْت | дом").kind == Kind.WORD


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
