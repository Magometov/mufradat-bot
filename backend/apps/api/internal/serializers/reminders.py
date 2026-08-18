from rest_framework import serializers

from apps.learning.models import CardState
from apps.vocabulary.services import postcard_url


class ReminderSerializer(serializers.Serializer):
    """Карточка для чата: кому и что отправить."""

    telegram_id = serializers.IntegerField(source="learner.telegram_id")
    arabic = serializers.CharField(source="card.arabic")
    translation_ru = serializers.CharField(source="card.translation_ru")
    transliteration = serializers.CharField(source="card.transliteration")
    # Собранная карточка, как в группе: слова нарисованы на ней, прятать нечего.
    image = serializers.SerializerMethodField()

    def get_image(self, state: CardState) -> str | None:
        return postcard_url(state.card)
