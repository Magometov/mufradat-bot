import logging

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.internal.permissions import IsBot
from apps.api.internal.serializers import GroupCardSerializer, GroupTakeSerializer
from apps.learning.services import take_group_card

logger = logging.getLogger(__name__)


class GroupCardView(APIView):
    """Отдаёт боту слово для группы и помечает его отправленным.

    Наступил ли слот, считает бэкенд: бот только отправляет, как и с напоминаниями.
    """

    permission_classes = (IsBot,)

    def post(self, request: Request) -> Response:
        data = GroupTakeSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        card = take_group_card(**data.validated_data)

        if card is None:
            return Response(status=status.HTTP_204_NO_CONTENT)

        logger.info("в группу уходит: %s", card)

        return Response(GroupCardSerializer(card).data)
