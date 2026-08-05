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


_ARABIC_LETTERS = re.compile(r"[ء-ي]+")

_DEFINITE_ARTICLE = "ال"

_PROCLITICS = ("و", "ف", "ب", "ل", "ك")


def _candidate_forms(token: str) -> list[str]:
    """Варианты одного токена, от точного к менее точному."""
    forms = [token]

    if token.startswith(_DEFINITE_ARTICLE) and len(token) > 3:
        forms.append(token[2:])

    for proclitic in _PROCLITICS:
        if token.startswith(proclitic) and len(token) > 2:
            rest = token[1:]
            forms.append(rest)
            if rest.startswith(_DEFINITE_ARTICLE) and len(rest) > 3:
                forms.append(rest[2:])

    return forms


def match_entries_in_sentence(sentence: str, known: dict[str, int]) -> set[int]:
    """Найти единицы словаря, использованные в предложении.

    `known` — отображение `Entry.arabic_norm` в id. Нужно потому, что в тексте слово
    идёт с артиклем и слитными предлогами, и прямое сравнение его не найдёт.
    """
    if not known:
        return set()

    matched: set[int] = set()
    for token in _ARABIC_LETTERS.findall(normalize_arabic(sentence)):
        # Полная форма проверяется первой: снятие первой буквы у слова, которое
        # просто с неё начинается, не должно побеждать точное попадание.
        for form in _candidate_forms(token):
            entry_id = known.get(form)
            if entry_id is not None:
                matched.add(entry_id)
                break

    return matched
