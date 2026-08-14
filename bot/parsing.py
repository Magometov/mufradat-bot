"""Разбор вставки: строки от владельца превращаются в карточки колоды."""

from dataclasses import dataclass

SEPARATOR = "|"

SINGULAR = 1
PLURAL = 2

# Число пишут как удобнее: и словом, и сокращением, и цифрой.
NUMBERS = {
    "ед": SINGULAR,
    "ед.": SINGULAR,
    "единственное": SINGULAR,
    "1": SINGULAR,
    "мн": PLURAL,
    "мн.": PLURAL,
    "множественное": PLURAL,
    "2": PLURAL,
}

WORD_COLUMNS = 5
PHRASE_COLUMNS = 4

REQUIRED = "русское и арабское обязательны"


class Broken(Exception):
    """Строку не разобрать: причина словами в сообщении."""


@dataclass(frozen=True, slots=True)
class Card:
    """Одна карточка колоды. Без числа — фраза: чисел у неё не бывает."""

    translation_ru: str
    transliteration: str
    arabic: str
    prompt: str
    number: int | None = None


@dataclass(slots=True)
class Group:
    """Единица вставки: слово со своими числами или одиночная фраза."""

    cards: list[Card]

    @property
    def title(self) -> str:
        """Подпись для списка: переводы всех карточек через дробь."""
        return " / ".join(card.translation_ru for card in self.cards)


@dataclass(frozen=True, slots=True)
class Problem:
    """Строка, которую не разобрать: её номер и причина."""

    line: int
    reason: str


@dataclass(frozen=True, slots=True)
class Parsed:
    """Что вышло из вставки. Хоть одна беда — вставку целиком не берут."""

    groups: list[Group]
    problems: list[Problem]


def _rows(text: str) -> list[tuple[int, list[str]]]:
    """Нумерует непустые строки и режет их по разделителю."""
    numbered = enumerate(text.splitlines(), start=1)

    return [
        (number, [part.strip() for part in line.split(SEPARATOR)])
        for number, line in numbered
        if line.strip()
    ]


def _word_card(parts: list[str]) -> Card:
    """Строка слова: пять столбцов, и число из них должно быть узнаваемо."""
    if len(parts) != WORD_COLUMNS:
        raise Broken(f"столбцов {len(parts)}, а нужно {WORD_COLUMNS}")

    translation_ru, written, transliteration, arabic, prompt = parts

    if not translation_ru or not arabic:
        raise Broken(REQUIRED)

    number = NUMBERS.get(written.lower())
    if number is None:
        raise Broken(f"число «{written}» не понял: пиши «ед» или «мн»")

    return Card(translation_ru, transliteration, arabic, prompt, number)


def _phrase_card(parts: list[str]) -> Card:
    """Строка фразы: четыре столбца, числа нет."""
    if len(parts) != PHRASE_COLUMNS:
        raise Broken(f"столбцов {len(parts)}, а нужно {PHRASE_COLUMNS}")

    translation_ru, transliteration, arabic, prompt = parts

    if not translation_ru or not arabic:
        raise Broken(REQUIRED)

    return Card(translation_ru, transliteration, arabic, prompt)


def _single(text: str) -> list[str]:
    """Единственная строка вставки, порезанная по разделителю."""
    rows = _rows(text)

    if len(rows) != 1:
        raise Broken(f"строк {len(rows)}, а нужна одна")

    return rows[0][1]


def parse_words(text: str) -> Parsed:
    """Разбирает слова: пять столбцов, «мн» цепляется к строке над ней."""
    groups: list[Group] = []
    problems: list[Problem] = []

    for line, parts in _rows(text):
        try:
            card = _word_card(parts)
        except Broken as error:
            problems.append(Problem(line, str(error)))
            continue

        if card.number == SINGULAR:
            groups.append(Group([card]))
            continue

        if not groups:
            problems.append(Problem(line, "множественное первой строкой: цеплять не к чему"))
            continue

        if any(taken.number == PLURAL for taken in groups[-1].cards):
            problems.append(Problem(line, "у слова над ней уже есть множественное"))
            continue

        groups[-1].cards.append(card)

    return Parsed(groups, problems)


def parse_phrases(text: str) -> Parsed:
    """Разбирает фразы: четыре столбца, каждая строка сама по себе."""
    groups: list[Group] = []
    problems: list[Problem] = []

    for line, parts in _rows(text):
        try:
            groups.append(Group([_phrase_card(parts)]))
        except Broken as error:
            problems.append(Problem(line, str(error)))

    return Parsed(groups, problems)


def one_word(text: str) -> Card:
    """Строка слова в одиночку: ею заменяют карточку на приёмке.

    Правила связи здесь не действуют — множественное приходит без соседа сверху,
    потому что заменяет уже стоящую в очереди форму.
    """
    return _word_card(_single(text))


def one_phrase(text: str) -> Card:
    """Строка фразы в одиночку — тем же порядком."""
    return _phrase_card(_single(text))
