from rest_framework import serializers


class VisitSerializer(serializers.Serializer):
    """Вход в приложение. Пустое тело — заход с сайта, о нём и рассказать нечего."""

    # Подписанная строка от клиента Telegram; из браузера её не приходит.
    init_data = serializers.CharField(required=False, allow_blank=True, default="")
    # Кто пришёл — словами бота: у него подписи нет, зато есть общий секрет.
    telegram_id = serializers.IntegerField(required=False, min_value=1)
    username = serializers.CharField(required=False, allow_blank=True, default="")
