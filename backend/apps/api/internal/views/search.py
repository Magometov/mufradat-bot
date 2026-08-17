from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.internal.permissions import IsBot
from apps.api.internal.serializers import FoundCardSerializer, SearchSerializer
from apps.vocabulary.constants import SEARCH_LIMIT
from apps.vocabulary.services import find


class SearchView(APIView):
    """Ищет карточки по русскому слову: этим бот отвечает в инлайне."""

    permission_classes = (IsBot,)

    def get(self, request: Request) -> Response:
        data = SearchSerializer(data=request.query_params)
        data.is_valid(raise_exception=True)
        cards = find(**data.validated_data, limit=SEARCH_LIMIT)

        return Response(FoundCardSerializer(cards, many=True).data)
