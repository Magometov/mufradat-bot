from django.conf import settings
from django.utils.crypto import constant_time_compare
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

HEADER = "X-Bot-Token"


class IsBot(BasePermission):
    """Пускает только бота — по общему секрету в заголовке."""

    message = f"Нужен заголовок {HEADER}."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Пустой токен в настройках не пускает никого: иначе ручки открыты всем."""
        token = settings.BOT_API_TOKEN

        return bool(token) and constant_time_compare(request.headers.get(HEADER, ""), token)
