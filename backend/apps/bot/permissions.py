from django.conf import settings


def is_admin(telegram_id: int) -> bool:
    """Единственное место, где решается вопрос о правах админа."""
    return bool(settings.ADMIN_TELEGRAM_ID) and telegram_id == settings.ADMIN_TELEGRAM_ID
