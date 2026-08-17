"""Формы слов по числу: сообщения бота склоняются, как человеческая речь."""

# Формы идут тройкой: для одного, для двух-четырёх и для остальных.
CARDS = ("карточки", "карточек", "карточек")


def plural(count: int, forms: tuple[str, str, str]) -> str:
    """Форма слова для этого числа."""
    tail = abs(count) % 100
    last = tail % 10

    if 10 < tail < 20:
        return forms[2]
    if last == 1:
        return forms[0]
    if 1 < last < 5:
        return forms[1]

    return forms[2]
