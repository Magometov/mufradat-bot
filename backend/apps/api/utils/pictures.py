"""Адреса картинок для бота.

Путь, а не полный адрес: собранный здесь, он взял бы внутренний хост, с которым бот
ходит к бэкенду, — а такую ссылку Telegram не скачает. Хост подставляет бот.
"""

from django.urls import reverse

from apps.vocabulary.models import Phrase, WordForm
from apps.vocabulary.utils import card_id


def postcard_path(card: WordForm | Phrase) -> str | None:
    """Собранная карточка. `None` — картинки нет, и собирать нечего."""
    return reverse("postcard", args=[card_id(card)]) if card.image else None


def photo_path(card: WordForm | Phrase) -> str | None:
    """Голая иллюстрация джипегом."""
    return reverse("photo", args=[card_id(card)]) if card.image else None
