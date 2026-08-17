"""Номер карточки для приложения: формы и фразы лежат в разных таблицах."""

WORD = "w"
PHRASE = "p"


def to_id(pk: int, *, is_word: bool) -> str:
    """Номер вида `w12` или `p7`: без буквы форма №5 и фраза №5 столкнулись бы."""
    return f"{WORD if is_word else PHRASE}{pk}"
