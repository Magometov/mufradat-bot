from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import CardSerializer
from apps.vocabulary.services import deck


class CardListView(APIView):
    """Колода одним ответом: формы слов и фразы плоским списком."""

    def get(self, request: Request) -> Response:
        cards = deck()

        return Response(CardSerializer(cards, many=True, context={"request": request}).data)
