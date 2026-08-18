"""Картинки для чата готовятся при сохранении карточки.

Сигнал, а не вызов из сервиса: карточку сохраняют бот, админка, формы чисел внутри
слова и разовые команды — перечислять их все значит однажды забыть одно место.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.vocabulary.models import Phrase, WordForm
from apps.vocabulary.services import Card, refresh_pictures


@receiver(post_save, sender=WordForm)
@receiver(post_save, sender=Phrase)
def prepare_pictures(sender: object, instance: Card, **kwargs: object) -> None:
    """Собирает карточку и иллюстрацию для чата, если их ещё нет."""
    refresh_pictures(instance)
