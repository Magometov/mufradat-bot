from django.conf import settings
from django.utils.crypto import constant_time_compare
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

HEADER = "X-Bot-Token"


def signed(request: Request) -> bool:
    """Запрос от бота: общий секрет в заголовке.

    Пустой токен в настройках не пускает никого: иначе ручки открыты всем.
    """
    token = settings.BOT_API_TOKEN

    return bool(token) and constant_time_compare(request.headers.get(HEADER, ""), token)


class IsBot(BasePermission):
    """Пускает только бота. Открытые ручки зовут `signed` напрямую: им отказывать нельзя."""

    message = f"Нужен заголовок {HEADER}."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return signed(request)
