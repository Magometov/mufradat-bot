from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import CardSerializer, ThemeSerializer
from apps.vocabulary.constants import Theme
from apps.vocabulary.models import Phrase, WordForm


class CardListView(APIView):
    """Колода одним ответом: формы слов и фразы плоским списком."""

    def get(self, request: Request) -> Response:
        forms = WordForm.objects.select_related("word").order_by(
            "-word__created_at", "-word_id", "number"
        )
        phrases = Phrase.objects.order_by("-created_at", "-id")
        cards = [*forms, *phrases]

        return Response(CardSerializer(cards, many=True, context={"request": request}).data)


class ThemeListView(APIView):
    """Разделы для кнопок на главной. Порядок в ответе — порядок кнопок."""

    def get(self, _: Request) -> Response:
        themes = [{"slug": slug, "name": label} for slug, label in Theme.choices]

        return Response(ThemeSerializer(themes, many=True).data)
