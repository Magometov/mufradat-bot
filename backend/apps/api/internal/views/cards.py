import logging

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.internal.permissions import IsBot
from apps.api.internal.serializers import FormSerializer, PhraseSerializer
from apps.vocabulary import services

logger = logging.getLogger(__name__)


class FormCreateView(APIView):
    """Добавляет форму слова. Новое слово заводится в разделе последнего урока."""

    permission_classes = (IsBot,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request: Request) -> Response:
        data = FormSerializer(data=request.data)
        data.is_valid(raise_exception=True)

        try:
            form = services.add_form(**data.validated_data)
        except services.Occupied as error:
            return Response({"detail": str(error)}, status=status.HTTP_409_CONFLICT)

        logger.info("бот добавил форму %s к слову %s", form.pk, form.word_id)

        return Response({"word": form.word_id}, status=status.HTTP_201_CREATED)


class PhraseCreateView(APIView):
    """Добавляет фразу — туда же, в раздел последнего урока."""

    permission_classes = (IsBot,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request: Request) -> Response:
        data = PhraseSerializer(data=request.data)
        data.is_valid(raise_exception=True)

        try:
            phrase = services.add_phrase(**data.validated_data)
        except services.Occupied as error:
            return Response({"detail": str(error)}, status=status.HTTP_409_CONFLICT)

        logger.info("бот добавил фразу %s", phrase.pk)

        return Response({"phrase": phrase.pk}, status=status.HTTP_201_CREATED)
