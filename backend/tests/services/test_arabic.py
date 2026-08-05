from apps.vocabulary.services.arabic import match_entries_in_sentence, normalize_arabic

# arabic_norm -> id единицы
KNOWN = {
    "كتاب": 1,
    "بيت": 2,
    "قمر": 3,
    "مدرسة": 4,
    "مدرس": 5,
    "كبير": 6,
}


def test_strips_diacritics() -> None:
    assert normalize_arabic("كِتَاب") == "كتاب"


def test_strips_shadda_and_damma() -> None:
    assert normalize_arabic("مُدَرِّسٌ") == "مدرس"


def test_strips_sukun_and_tanwin() -> None:
    assert normalize_arabic("بَيْتٌ") == "بيت"


def test_unifies_alef_with_hamza() -> None:
    assert normalize_arabic("أَحْمَد") == "احمد"
    assert normalize_arabic("إِسْلَام") == "اسلام"
    assert normalize_arabic("آسِف") == "اسف"


def test_unifies_alef_maqsura_to_ya() -> None:
    assert normalize_arabic("عَلَى") == "علي"


def test_keeps_ta_marbuta_distinct_from_ha() -> None:
    assert normalize_arabic("مَدْرَسَة") == "مدرسة"
    assert normalize_arabic("مَدْرَسَة") != normalize_arabic("مدرسه")


def test_strips_tatweel() -> None:
    assert normalize_arabic("كــتاب") == "كتاب"


def test_collapses_whitespace() -> None:
    assert normalize_arabic("  بَيْتٌ   كَبِيرٌ  ") == "بيت كبير"


def test_is_idempotent() -> None:
    once = normalize_arabic("الْمُدَرِّسُ")
    assert normalize_arabic(once) == once


def test_empty_string() -> None:
    assert normalize_arabic("") == ""


def test_non_arabic_passes_through() -> None:
    assert normalize_arabic("hello") == "hello"


def test_gender_pairs_collapse_and_that_is_expected() -> None:
    """Фиксирует слепоту, вокруг которой построена модель (§4.1 спеки).

    Обращение к мужчине и к женщине различается только последней харакой, а её
    нормализация снимает. Поэтому уникальность в БД стоит на точном `arabic`, а
    различает пару поле `Entry.person`.
    """
    assert normalize_arabic("مَا اسْمُكَ؟") == normalize_arabic("مَا اسْمُكِ؟")
    assert normalize_arabic("كَتَبْتَ") == normalize_arabic("كَتَبْتِ")


def test_matches_bare_word() -> None:
    assert match_entries_in_sentence("هَذَا بَيْتٌ", KNOWN) == {2}


def test_matches_word_with_definite_article() -> None:
    assert match_entries_in_sentence("الْكِتَابُ هُنَا", KNOWN) == {1}


def test_matches_word_with_conjunction_and_article() -> None:
    assert match_entries_in_sentence("وَالْقَمَرُ", KNOWN) == {3}


def test_matches_several_words_in_one_sentence() -> None:
    assert match_entries_in_sentence("الْمُدَرِّسُ فِي الْمَدْرَسَةِ", KNOWN) == {4, 5}


def test_full_form_wins_over_stripped_prefix() -> None:
    """بيت должно совпасть целиком, а не разобраться как ب + يت."""
    assert match_entries_in_sentence("بَيْت", KNOWN) == {2}


def test_unknown_words_are_ignored() -> None:
    assert match_entries_in_sentence("هَذَا شَيْءٌ غَرِيبٌ", KNOWN) == set()


def test_punctuation_does_not_break_matching() -> None:
    assert match_entries_in_sentence("هَذَا بَيْتٌ كَبِيرٌ.", KNOWN) == {2, 6}


def test_empty_sentence() -> None:
    assert match_entries_in_sentence("", KNOWN) == set()


def test_empty_dictionary() -> None:
    assert match_entries_in_sentence("الْكِتَابُ", {}) == set()
