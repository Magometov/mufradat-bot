from rest_framework import serializers

from apps.learning.models import CardState
from apps.vocabulary.services import photo_url


class ReminderSerializer(serializers.Serializer):
    """Карточка для чата: кому и что отправить."""

    telegram_id = serializers.IntegerField(source="learner.telegram_id")
    arabic = serializers.CharField(source="card.arabic")
    translation_ru = serializers.CharField(source="card.translation_ru")
    transliteration = serializers.CharField(source="card.transliteration")
    # Голая иллюстрация, а не собранная карточка: спойлер прячет ответ, а на собранной
    # он написан.
    image = serializers.SerializerMethodField()
    # Первое сообщение человеку идёт со вступлением.
    is_first = serializers.BooleanField()

    def get_image(self, state: CardState) -> str | None:
        return photo_url(state.card)
