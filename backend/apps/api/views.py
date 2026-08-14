from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import CardSerializer, ThemeSerializer
from apps.vocabulary import services
from apps.vocabulary.constants import Theme


class CardListView(APIView):
    """Колода одним ответом: формы слов и фразы плоским списком."""

    def get(self, request: Request) -> Response:
        cards = services.deck()

        return Response(CardSerializer(cards, many=True, context={"request": request}).data)


class ThemeListView(APIView):
    """Разделы для кнопок на главной. Порядок в ответе — порядок кнопок."""

    def get(self, _: Request) -> Response:
        themes = [{"slug": slug, "name": label} for slug, label in Theme.choices]

        return Response(ThemeSerializer(themes, many=True).data)
