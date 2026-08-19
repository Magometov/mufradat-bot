from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.api.serializers import AnswerListSerializer, CardStateSerializer
from apps.common.constants import INIT_DATA_HEADER
from apps.common.services import visitor
from apps.learning.constants import Verdict
from apps.learning.services import apply
from apps.learning.utils import presses
from apps.vocabulary.services import cards_by_id


class AnswerCreateView(APIView):
    """Принимает пачку оценок и отвечает новыми состояниями карточек."""

    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "answers"

    def post(self, request: Request) -> Response:
        _, learner = visitor(init_data=request.headers.get(INIT_DATA_HEADER, ""))

        if learner is None:
            raise PermissionDenied("Оценки принимаются только от опознанного человека.")

        data = AnswerListSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        answers = data.validated_data["answers"]

        # Номер мог остаться от карточки, удалённой из колоды: такую оценку пропускаем,
        # а остальную пачку применяем.
        cards = cards_by_id(answer["card_id"] for answer in answers)
        moments = presses([answer["answered_at"] for answer in answers], timezone.now())

        with transaction.atomic():
            states = [
                apply(
                    learner=learner,
                    card=cards[answer["card_id"]],
                    knows=answer["verdict"] == Verdict.KNOW,
                    now=moment,
                )
                for answer, moment in zip(answers, moments, strict=True)
                if answer["card_id"] in cards
            ]

        return Response(CardStateSerializer(states, many=True).data)
