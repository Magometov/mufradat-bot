import logging

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.internal.permissions import IsBot
from apps.api.internal.serializers import (
    LearnerSerializer,
    ProgressSerializer,
    ReminderSerializer,
)
from apps.common.services import identify
from apps.learning.services import summary, switch_reminders, take_reminders

logger = logging.getLogger(__name__)


class ReminderTakeView(APIView):
    """Отдаёт боту по одной карточке на человека и помечает их отправленными.

    Окно тишины и шаг между сообщениями считает бэкенд: бот только отправляет.
    """

    permission_classes = (IsBot,)

    def post(self, request: Request) -> Response:
        cards = take_reminders()

        if cards:
            logger.info("к отправке в чат: %s", len(cards))

        return Response(ReminderSerializer(cards, many=True).data)


class RemindersSwitchView(APIView):
    """Переворачивает признак напоминаний.

    Переключает сама, а не принимает нужное состояние: боту тогда не надо спрашивать
    текущее, и два быстрых нажатия не спорят друг с другом.
    """

    permission_classes = (IsBot,)

    def post(self, request: Request) -> Response:
        data = LearnerSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        learner = identify(**data.validated_data)
        learner = switch_reminders(learner, on=not learner.reminders_on)
        logger.info("напоминания у %s: %s", learner.telegram_id, learner.reminders_on)

        return Response(ProgressSerializer(summary(learner)).data)
