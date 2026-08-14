from datetime import datetime
from itertools import chain
from typing import Any

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import CardSerializer, ThemeSerializer
from apps.vocabulary.cards import card_id
from apps.vocabulary.models import Phrase, WordForm
from apps.vocabulary.themes import Theme


class CardListView(APIView):
    """Колода одним ответом: формы слов и фразы плоским списком, новые первыми."""

    def get(self, request: Request) -> Response:
        forms = WordForm.objects.select_related("word")
        cards = sorted(chain(forms, Phrase.objects.all()), key=_order, reverse=True)

        return Response(CardSerializer([_card(card, request) for card in cards], many=True).data)


class ThemeListView(APIView):
    """Темы для кнопок на главной."""

    def get(self, request: Request) -> Response:
        themes = [{"slug": slug, "name": label} for slug, label in Theme.choices]

        return Response(ThemeSerializer(themes, many=True).data)


def _order(card: WordForm | Phrase) -> tuple[datetime, int, int]:
    """Порядок колоды: новые первыми, а внутри слова — единственное число."""
    if isinstance(card, WordForm):
        return (card.word.created_at, card.word.pk, -card.number)

    return (card.created_at, card.pk, 0)


def _card(card: WordForm | Phrase, request: Request) -> dict[str, Any]:
    """Карточка для приложения. Тип и есть ответ на вопрос «слово ли это»."""
    return {
        "id": card_id(card),
        "arabic": card.arabic,
        "translation_ru": card.translation_ru,
        "transliteration": card.transliteration,
        "is_word": isinstance(card, WordForm),
        "image": request.build_absolute_uri(card.image.url) if card.image else None,
        "themes": card.themes,
    }
