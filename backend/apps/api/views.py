from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import EntrySerializer, ThemeSerializer
from apps.vocabulary.models import Entry
from apps.vocabulary.themes import Theme


class EntryListView(ListAPIView):
    """View для колоды карточек."""

    serializer_class = EntrySerializer
    queryset = Entry.objects.order_by("-created_at", "-id")


class ThemeListView(APIView):
    """Темы для кнопок на главной."""

    def get(self, request: Request) -> Response:
        themes = [{"slug": slug, "name": label} for slug, label in Theme.choices]

        return Response(ThemeSerializer(themes, many=True).data)
