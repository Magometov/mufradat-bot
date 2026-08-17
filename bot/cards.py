"""Подпись к карточке: разметка одна на все чаты, шаблон у каждого свой."""

import html


def caption(template: str, *, arabic: str, translation: str, transliteration: str) -> str:
    """Подставляет слова в шаблон.

    Экранирует: сообщения уходят разметкой, и «&» или «<» в переводе иначе ломают её —
    Telegram отказывается разбирать такое сообщение целиком. Пустая транслитерация не
    оставляет за собой пустой строки.
    """
    translit = f"\n{html.escape(transliteration)}" if transliteration else ""

    return template.format(
        arabic=html.escape(arabic),
        translation=html.escape(translation),
        transliteration=translit,
    )
