from rest_framework import serializers

from apps.vocabulary.models import Phrase, WordForm


class CardSerializer(serializers.Serializer):
    """Карточка колоды: форма слова и фраза едут в приложение одинаково."""

    id = serializers.SerializerMethodField()
    arabic = serializers.CharField()
    translation_ru = serializers.CharField()
    transliteration = serializers.CharField()
    is_word = serializers.SerializerMethodField()
    image = serializers.ImageField()
    themes = serializers.ListField(child=serializers.CharField())

    def get_id(self, card: WordForm | Phrase) -> str:
        """Формы и фразы лежат в разных таблицах: без буквы форма №5 и фраза №5
        столкнулись бы, а прогон в браузере ссылается как раз на номер."""
        return f"{'w' if self.get_is_word(card) else 'p'}{card.pk}"

    def get_is_word(self, card: WordForm | Phrase) -> bool:
        """Тип карточки и есть ответ: флага в базе для этого больше нет."""
        return isinstance(card, WordForm)


class ThemeSerializer(serializers.Serializer):
    """Раздел колоды: код для фильтра и подпись для кнопки."""

    slug = serializers.CharField()
    name = serializers.CharField()


class VisitSerializer(serializers.Serializer):
    """Вход в приложение. Пустое тело — заход с сайта, о нём и рассказать нечего."""

    # Подписанная строка от клиента Telegram; из браузера её не приходит.
    init_data = serializers.CharField(required=False, allow_blank=True, default="")
    # Кто пришёл — словами бота: у него подписи нет, зато есть общий секрет.
    telegram_id = serializers.IntegerField(required=False, min_value=1)
    username = serializers.CharField(required=False, allow_blank=True, default="")
