import logging

from django.shortcuts import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.internal.permissions import IsBot
from apps.api.internal.serializers import MoveSerializer
from apps.vocabulary.models import Word
from apps.vocabulary.services import (
    UNITS,
    lesson_phrases,
    lesson_words,
    move_from_lesson,
    move_targets,
)

logger = logging.getLogger(__name__)


def _word_title(word: Word) -> str:
    """Подпись слова для бота: переводы всех форм по порядку числа."""
    return " / ".join(form.translation_ru for form in word.forms.all()) or str(word)


class LessonView(APIView):
    """Что лежит в разделе последнего урока и по каким темам это можно разложить."""

    permission_classes = (IsBot,)

    def get(self, _: Request) -> Response:
        units = [
            *(
                {"kind": "word", "id": word.pk, "title": _word_title(word)}
                for word in lesson_words()
            ),
            *(
                {"kind": "phrase", "id": phrase.pk, "title": phrase.translation_ru}
                for phrase in lesson_phrases()
            ),
        ]
        themes = [{"slug": slug, "name": name} for slug, name in move_targets()]

        return Response({"units": units, "themes": themes})


class LessonMoveView(APIView):
    """Выносит единицу из раздела урока в выбранные темы. Пустой список — без тем."""

    permission_classes = (IsBot,)

    def post(self, request: Request) -> Response:
        data = MoveSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        fields = data.validated_data

        unit = get_object_or_404(UNITS[fields["kind"]], pk=fields["id"])
        themes = move_from_lesson(unit, fields["themes"])
        logger.info("бот разложил %s %s → %s", fields["kind"], unit.pk, themes or "без темы")

        return Response({"themes": themes})
