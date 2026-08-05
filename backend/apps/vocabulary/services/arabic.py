import re
import unicodedata

_DIACRITICS = re.compile(r"[ً-ٰٟۖ-ۭ]")

_TATWEEL = "ـ"

_LETTER_FOLDING = str.maketrans(
    {
        "أ": "ا",  # أ -> ا
        "إ": "ا",  # إ -> ا
        "آ": "ا",  # آ -> ا
        "ٱ": "ا",  # ٱ -> ا
        "ى": "ي",  # ى -> ي
    }
)


def normalize_arabic(text: str) -> str:
    """Привести арабское слово к ключу для поиска похожих записей.

    Огласовки хранятся как распознаны, но в ключ не входят: модель может вернуть то
    же слово с иной расстановкой харакат. Формы, различающиеся только последней
    харакой, дают один ключ — поэтому уникальность в БД стоит на точном `arabic`.
    """
    text = unicodedata.normalize("NFC", text)
    text = _DIACRITICS.sub("", text)
    text = text.replace(_TATWEEL, "")
    # ة и ه не объединяются: это меняет смысл слова.
    text = text.translate(_LETTER_FOLDING)
    return " ".join(text.split())
