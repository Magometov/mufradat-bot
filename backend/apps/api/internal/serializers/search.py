from rest_framework import serializers

from apps.api.utils import postcard_path
from apps.vocabulary.models import Phrase, WordForm
from apps.vocabulary.utils import card_id


class SearchSerializer(serializers.Serializer):
    """Запрос поиска: слово по-русски. Потолок ответа не спрашивают, он один на всех."""

    query = serializers.CharField(required=False, allow_blank=True, default="")


class FoundCardSerializer(serializers.Serializer):
    """Найденная карточка: из этого бот собирает ответ инлайна."""

    id = serializers.SerializerMethodField()
    arabic = serializers.CharField()
    translation_ru = serializers.CharField()
    transliteration = serializers.CharField()
    # Собранная карточка, а не иллюстрация: в инлайне уезжает именно она.
    image = serializers.SerializerMethodField()

    def get_id(self, card: WordForm | Phrase) -> str:
        return card_id(card)

    def get_image(self, card: WordForm | Phrase) -> str | None:
        return postcard_path(card)
