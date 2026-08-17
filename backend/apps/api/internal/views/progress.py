import logging

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.internal.permissions import IsBot
from apps.api.internal.serializers import LearnerSerializer, ProgressSerializer
from apps.common.models import Learner
from apps.common.services import identify
from apps.learning.services import count_states, reset_progress
from apps.learning.utils import enabled

logger = logging.getLogger(__name__)


def learner_from(data: dict) -> Learner:
    """Человек из апдейта бота. Заводится сам: команда может прийти раньше первого захода."""
    return identify(telegram_id=data["telegram_id"], username=data["username"])


def progress_of(learner: Learner) -> Response:
    """Сводка, которой бот отвечает на команды."""
    return Response(
        ProgressSerializer(
            {
                "reminders_on": learner.reminders_on,
                "scheduling": enabled(learner),
                "cards": count_states(learner),
            }
        ).data
    )


class ProgressView(APIView):
    """Что у человека с прогрессом: этим бот отвечает на команды."""

    permission_classes = (IsBot,)

    def post(self, request: Request) -> Response:
        data = LearnerSerializer(data=request.data)
        data.is_valid(raise_exception=True)

        return progress_of(learner_from(data.validated_data))


class ProgressResetView(APIView):
    """Обнуляет прогресс. Колоду не трогает: карточки остаются, уходят только уровни."""

    permission_classes = (IsBot,)

    def post(self, request: Request) -> Response:
        data = LearnerSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        learner = learner_from(data.validated_data)
        cleared = reset_progress(learner)
        logger.info("прогресс у %s сброшен: %s карточек", learner.telegram_id, cleared)

        return progress_of(learner)
