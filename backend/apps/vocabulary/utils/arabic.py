"""Арабское для рисования: Pillow в контейнере собран без raqm и вязь не строит сам."""

import arabic_reshaper
from bidi import get_display

# Огласовки не выбрасываем: колода хранит их намеренно, ради них слово и читают.
_reshaper = arabic_reshaper.ArabicReshaper(configuration={"delete_harakat": False})


def for_drawing(text: str) -> str:
    """Соединяет буквы и разворачивает строку справа налево.

    Без этого Pillow рисует каждую букву отдельной формой и слева направо — слово
    рассыпается и читается задом наперёд.
    """
    return get_display(_reshaper.reshape(text))
