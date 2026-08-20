from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.internal.permissions import IsBot
from apps.api.internal.serializers import CardPairSerializer, KnownSerializer
from apps.vocabulary.services import known_cards


class KnownView(APIView):
    """Что из присланного уже в колоде. Бот спрашивает до того, как рисовать картинки."""

    permission_classes = (IsBot,)

    def post(self, request: Request) -> Response:
        data = KnownSerializer(data=request.data)
        data.is_valid(raise_exception=True)

        pairs = [(card["arabic"], card["translation_ru"]) for card in data.validated_data["cards"]]
        known = [
            {"arabic": arabic, "translation_ru": translation}
            for arabic, translation in known_cards(pairs)
        ]

        return Response({"known": CardPairSerializer(known, many=True).data})
