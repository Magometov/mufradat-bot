from django.conf import settings
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import StateSerializer
from apps.common.constants import INIT_DATA_HEADER
from apps.common.services import visitor
from apps.learning.services import states
from apps.learning.utils import enabled


class StateView(APIView):
    """Прогресс того, кто спросил, и правила расписания. Неопознанному — только правила."""

    def get(self, request: Request) -> Response:
        _, learner = visitor(init_data=request.headers.get(INIT_DATA_HEADER, ""))

        state = {
            "enabled": enabled(learner),
            "now": timezone.now(),
            "ladder": settings.LADDER,
            "jitter": settings.JITTER_PERCENT,
            "first_sight_level": settings.FIRST_SIGHT_LEVEL,
            "needed": settings.SIDES_NEEDED,
            "lapse_drop": settings.LAPSE_DROP,
            "answers_limit": settings.ANSWERS_LIMIT,
            "cards": states(learner) if learner is not None else [],
        }

        return Response(StateSerializer(state).data)
