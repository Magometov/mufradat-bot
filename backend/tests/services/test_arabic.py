from apps.vocabulary.services.arabic import normalize_arabic


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
