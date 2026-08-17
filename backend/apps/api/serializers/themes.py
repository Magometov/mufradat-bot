from rest_framework import serializers


class ThemeSerializer(serializers.Serializer):
    """Раздел колоды: код для фильтра и подпись для кнопки."""

    slug = serializers.CharField()
    name = serializers.CharField()
