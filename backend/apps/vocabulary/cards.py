"""Номер карточки: формы слов и фразы лежат в разных таблицах, и номера у них
сталкиваются. Буква разводит их везде, где карточки идут одним списком."""

from apps.vocabulary.models import Phrase, WordForm

WORD = "w"
PHRASE = "p"


def card_id(card: WordForm | Phrase) -> str:
    """Номер карточки — тот же в колоде приложения и в `--only` у команд."""
    return f"{WORD if isinstance(card, WordForm) else PHRASE}{card.pk}"


def split_ids(text: str) -> tuple[list[int], list[int]]:
    """Разбирает «w12,p7» на номера форм и номера фраз."""
    forms: list[int] = []
    phrases: list[int] = []

    for raw in text.split(","):
        part = raw.strip().lower()
        if not part:
            continue

        prefix, number = part[0], part[1:]
        if not number.isdigit() or prefix not in (WORD, PHRASE):
            raise ValueError(f"не номер карточки: «{part}». Ожидаю w12 или p7")

        (forms if prefix == WORD else phrases).append(int(number))

    return forms, phrases
