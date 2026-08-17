from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.internal.permissions import signed
from apps.api.serializers import CardSerializer, ThemeSerializer, VisitSerializer
from apps.common.constants import Source
from apps.common.models import Learner
from apps.common.services import learners, visits
from apps.common.utils import telegram
from apps.vocabulary import services
from apps.vocabulary.constants import Theme


def visitor(request: Request, fields: dict) -> tuple[Source, Learner | None]:
    """Кто пришёл: по подписи Telegram, по секрету бота или никак — тогда это сайт."""
    user = telegram.user_from(fields["init_data"])

    if user is not None:
        telegram_id, username = user

        return Source.TELEGRAM, learners.identify(telegram_id=telegram_id, username=username)

    # Полям тела верим только от бота: ручка открыта наружу, подписи у них нет.
    if signed(request) and fields.get("telegram_id"):
        learner = learners.identify(
            telegram_id=fields["telegram_id"],
            username=fields["username"],
        )

        return Source.TELEGRAM, learner

    return Source.SITE, None


class CardListView(APIView):
    """Колода одним ответом: формы слов и фразы плоским списком."""

    def get(self, request: Request) -> Response:
        cards = services.deck()

        return Response(CardSerializer(cards, many=True, context={"request": request}).data)


class ThemeListView(APIView):
    """Разделы для кнопок на главной. Порядок в ответе — порядок кнопок."""

    def get(self, _: Request) -> Response:
        themes = [{"slug": slug, "name": label} for slug, label in Theme.choices]

        return Response(ThemeSerializer(themes, many=True).data)


class VisitCreateView(APIView):
    """Пишет вход: из Telegram — с ником и id, из браузера — только факт и устройство."""

    def post(self, request: Request) -> Response:
        data = VisitSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        source, learner = visitor(request, data.validated_data)

        visits.log(
            source=source,
            learner=learner,
            user_agent=request.headers.get("User-Agent", ""),
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
