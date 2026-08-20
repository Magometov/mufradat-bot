import logging

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.internal.permissions import IsBot
from apps.api.internal.serializers import LearnerSerializer, ProgressSerializer
from apps.common.services import identify
from apps.learning.services import reset_progress, summary

logger = logging.getLogger(__name__)


class ProgressView(APIView):
    """Что у человека с прогрессом: этим бот отвечает на команды."""

    permission_classes = (IsBot,)

    def post(self, request: Request) -> Response:
        data = LearnerSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        learner = identify(**data.validated_data)

        return Response(ProgressSerializer(summary(learner)).data)


class ProgressResetView(APIView):
    """Обнуляет прогресс. Колоду не трогает: карточки остаются, уходят только уровни."""

    permission_classes = (IsBot,)

    def post(self, request: Request) -> Response:
        data = LearnerSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        learner = identify(**data.validated_data)
        cleared = reset_progress(learner)
        logger.info("прогресс у %s сброшен: %s карточек", learner.telegram_id, cleared)

        return Response(ProgressSerializer(summary(learner)).data)
