from apps.vocabulary.kind import is_word


def test_one_arabic_word_is_a_word() -> None:
    assert is_word("بَيْت", "дом") is True


def test_two_words_on_both_sides_are_a_phrase() -> None:
    assert is_word("هَذَا بَيْتٌ", "это дом") is False


def test_one_arabic_word_stays_a_word_with_a_long_translation() -> None:
    """Одним русским словом переводится не всё: «доска» — это «классная доска»."""
    assert is_word("سَبُّورَة", "классная доска") is True
    assert is_word("يَتَوَضَّأُ", "совершает малое омовение") is True


def test_synonyms_in_the_translation_do_not_make_a_phrase() -> None:
    """Перевод через запятую — два варианта одного слова, а не два слова."""
    assert is_word("قَصِير", "низкий, короткий") is True


def test_set_expression_with_a_one_word_translation_is_a_word() -> None:
    """Устойчивое выражение из двух арабских слов по смыслу — одно слово."""
    assert is_word("مِنْ أَيْنَ", "откуда") is True


def test_grammar_note_is_not_counted_as_translation() -> None:
    """Пометка в скобках — комментарий к форме, а не содержание карточки."""
    assert is_word("السَّلَامُ عَلَيْكَ", "здравствуй (к мужчине)") is True


def test_extra_spaces_do_not_make_a_phrase() -> None:
    assert is_word("  بَيْت  ", "  дом  ") is True
