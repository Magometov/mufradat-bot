from rest_framework.generics import ListAPIView

from apps.api.serializers import EntrySerializer
from apps.vocabulary.models import Entry


class EntryListView(ListAPIView):
    """Вся колода одним ответом.

    Постраничности нет намеренно: прогон — это снимок, взятый одним запросом, а
    тасует, фильтрует и выбирает сторону карточки приложение. Порядок задан, чтобы
    ответ не плавал от запроса к запросу.
    """

    serializer_class = EntrySerializer
    queryset = Entry.objects.order_by("-created_at", "-id")
