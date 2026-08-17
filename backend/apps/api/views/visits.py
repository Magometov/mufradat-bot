from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.api.internal.permissions import signed
from apps.api.serializers import VisitSerializer
from apps.common.services import learners, visits


class VisitCreateView(APIView):
    """Пишет вход: из Telegram — с человеком, из браузера — только факт и устройство."""

    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "visits"

    def post(self, request: Request) -> Response:
        data = VisitSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        fields = data.validated_data

        source, learner = learners.visitor(
            init_data=fields["init_data"],
            telegram_id=fields.get("telegram_id"),
            username=fields["username"],
            is_bot=signed(request),
        )

        visits.log(
            source=source,
            learner=learner,
            user_agent=request.headers.get("User-Agent", ""),
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
