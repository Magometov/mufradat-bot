import re
from dataclasses import dataclass

SEPARATOR = "|"

_ARABIC = re.compile(r"[؀-ۿ]")
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")

# ИИ охотно нумерует список и выделяет слова жирным, а промпт — это просьба, не
# гарантия. Без чистки «1.» и «**» уезжали внутрь арабского поля и вставали в колоду
# молча: карточка показывала «1. بَيْت».
_LIST_MARKER = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")
_DECORATION = str.maketrans("", "", "*`")


class ParseError(Exception):
    """Строка не разобралась; текст исключения уходит пользователю как есть."""


@dataclass(frozen=True)
class ParsedEntry:
    arabic: str
    translation_ru: str
    transliteration: str


def parse_entry(text: str) -> ParsedEntry:
    """Разобрать строку вида `بَيْت | дом | bayt`.

    Порядок частей не важен: арабский, русский и латиница лежат в разных диапазонах
    Unicode, поэтому сторона определяется алфавитом, а не позицией.
    """
    line = _LIST_MARKER.sub("", text)
    parts = [part.translate(_DECORATION).strip() for part in line.split(SEPARATOR)]
    parts = [part for part in parts if part]

    if len(parts) < 2:
        raise ParseError(f"Нужны хотя бы две части, разделённые «{SEPARATOR}»: арабское и перевод.")
    if len(parts) > 3:
        raise ParseError("Частей больше трёх — ожидаю арабское, перевод и транслитерацию.")

    arabic = [part for part in parts if _ARABIC.search(part)]
    if not arabic:
        raise ParseError("Не вижу арабского текста ни в одной части.")
    if len(arabic) > 1:
        raise ParseError("Все части арабские — не хватает перевода.")

    rest = [part for part in parts if part not in arabic]
    translation, transliteration = _split_rest(rest)

    return ParsedEntry(
        arabic=arabic[0],
        translation_ru=translation,
        transliteration=transliteration,
    )


def _split_rest(rest: list[str]) -> tuple[str, str]:
    """Разделить оставшиеся части на перевод и транслитерацию."""
    if not rest:
        raise ParseError("Не хватает перевода.")
    if len(rest) == 1:
        return rest[0], ""

    cyrillic = [part for part in rest if _CYRILLIC.search(part)]
    if len(cyrillic) == 1:
        other = next(part for part in rest if part is not cyrillic[0])
        return cyrillic[0], other
    # Кириллицы нет или она в обеих частях — сохраняем порядок, как набрали.
    return rest[0], rest[1]
