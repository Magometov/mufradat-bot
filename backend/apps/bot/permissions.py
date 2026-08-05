from django.conf import settings


def is_admin(telegram_id: int) -> bool:
    """Единственное место, где решается вопрос о правах админа."""
    return telegram_id in settings.ADMIN_TELEGRAM_IDS
