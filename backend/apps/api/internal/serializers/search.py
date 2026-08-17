from rest_framework import serializers

from apps.vocabulary.models import Phrase, WordForm
from apps.vocabulary.utils import to_id


class SearchSerializer(serializers.Serializer):
    """Запрос поиска: слово по-русски. Потолок ответа не спрашивают, он один на всех."""

    query = serializers.CharField(required=False, allow_blank=True, default="")


class FoundCardSerializer(serializers.Serializer):
    """Найденная карточка: из этого бот собирает ответ инлайна."""

    id = serializers.SerializerMethodField()
    arabic = serializers.CharField()
    translation_ru = serializers.CharField()
    transliteration = serializers.CharField()
    # Путь, а не полный адрес: он собрался бы от внутреннего хоста, а такую ссылку
    # Telegram не скачает. Публичный адрес подставляет бот — он его знает.
    image = serializers.ImageField()
    # Размеры едут, чтобы Telegram разложил список выбора, не скачивая картинки.
    image_width = serializers.IntegerField(allow_null=True)
    image_height = serializers.IntegerField(allow_null=True)

    def get_id(self, card: WordForm | Phrase) -> str:
        """Номер тот же, что у приложения: форма и фраза лежат в разных таблицах."""
        return to_id(card.pk, is_word=isinstance(card, WordForm))
