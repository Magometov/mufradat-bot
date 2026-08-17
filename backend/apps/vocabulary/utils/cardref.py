"""Номер карточки для приложения: формы и фразы лежат в разных таблицах."""

import re

from apps.vocabulary.models import Phrase, WordForm

WORD = "w"
PHRASE = "p"

PATTERN = re.compile(rf"^([{WORD}{PHRASE}])(\d+)$")


def to_id(pk: int, *, is_word: bool) -> str:
    """Номер вида `w12` или `p7`: без буквы форма №5 и фраза №5 столкнулись бы."""
    return f"{WORD if is_word else PHRASE}{pk}"


def card_id(card: WordForm | Phrase) -> str:
    """Номер готовой карточки: тип и есть ответ на вопрос, слово это или фраза."""
    return to_id(card.pk, is_word=isinstance(card, WordForm))


def parse(card_id: str) -> tuple[bool, int] | None:
    """Разбирает номер на «это форма» и число. `None` — номер не наш."""
    found = PATTERN.match(card_id)

    if found is None:
        return None

    return found.group(1) == WORD, int(found.group(2))
