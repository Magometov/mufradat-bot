from rest_framework import serializers

from apps.vocabulary.models import Phrase, WordForm
from apps.vocabulary.utils import to_id


class CardSerializer(serializers.Serializer):
    """Карточка колоды: форма слова и фраза едут в приложение одинаково."""

    id = serializers.SerializerMethodField()
    arabic = serializers.CharField()
    translation_ru = serializers.CharField()
    transliteration = serializers.CharField()
    is_word = serializers.SerializerMethodField()
    image = serializers.ImageField()
    image_width = serializers.IntegerField(allow_null=True)
    image_height = serializers.IntegerField(allow_null=True)
    themes = serializers.ListField(child=serializers.CharField())

    def get_id(self, card: WordForm | Phrase) -> str:
        return to_id(card.pk, is_word=self.get_is_word(card))

    def get_is_word(self, card: WordForm | Phrase) -> bool:
        """Тип карточки и есть ответ: флага в базе для этого больше нет."""
        return isinstance(card, WordForm)
