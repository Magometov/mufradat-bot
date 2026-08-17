from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import ThemeSerializer
from apps.vocabulary.constants import Theme


class ThemeListView(APIView):
    """Разделы для кнопок на главной. Порядок в ответе — порядок кнопок."""

    def get(self, _: Request) -> Response:
        themes = [{"slug": slug, "name": label} for slug, label in Theme.choices]

        return Response(ThemeSerializer(themes, many=True).data)
