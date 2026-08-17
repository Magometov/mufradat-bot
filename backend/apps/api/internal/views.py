import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.internal.permissions import IsBot
from apps.api.internal.serializers import (
    FormSerializer,
    MoveSerializer,
    PhraseSerializer,
    ReminderSerializer,
)
from apps.learning.services import take_reminders
from apps.vocabulary import services
from apps.vocabulary.models import Word

logger = logging.getLogger(__name__)


def word_title(word: Word) -> str:
    """Подпись слова для бота: переводы всех форм по порядку числа."""
    return " / ".join(form.translation_ru for form in word.forms.all()) or str(word)


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


class LessonView(APIView):
    """Что лежит в разделе последнего урока и по каким темам это можно разложить."""

    permission_classes = (IsBot,)

    def get(self, _: Request) -> Response:
        units = [
            *(
                {"kind": "word", "id": word.pk, "title": word_title(word)}
                for word in services.lesson_words()
            ),
            *(
                {"kind": "phrase", "id": phrase.pk, "title": phrase.translation_ru}
                for phrase in services.lesson_phrases()
            ),
        ]
        themes = [{"slug": slug, "name": name} for slug, name in services.move_targets()]

        return Response({"units": units, "themes": themes})


class LessonMoveView(APIView):
    """Выносит единицу из раздела урока в выбранные темы. Пустой список — без тем."""

    permission_classes = (IsBot,)

    def post(self, request: Request) -> Response:
        data = MoveSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        fields = data.validated_data

        unit = get_object_or_404(services.UNITS[fields["kind"]], pk=fields["id"])
        themes = services.move_from_lesson(unit, fields["themes"])
        logger.info("бот разложил %s %s → %s", fields["kind"], unit.pk, themes or "без темы")

        return Response({"themes": themes})


class ReminderTakeView(APIView):
    """Отдаёт боту по одной карточке на человека и помечает их отправленными.

    Окно тишины и шаг между сообщениями считает бэкенд: бот только отправляет.
    """

    permission_classes = (IsBot,)

    def post(self, request: Request) -> Response:
        cards = take_reminders()

        if cards:
            logger.info("к отправке в чат: %s", len(cards))

        return Response(ReminderSerializer(cards, many=True, context={"request": request}).data)
