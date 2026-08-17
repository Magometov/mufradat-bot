"""Выборки состояний и отправленного в группу: здесь же знание о том, как устроены поля."""

from django.db import models

from apps.vocabulary.models import Phrase, WordForm

# Карточка колоды: форма слова или фраза. Имя `Card` занято абстрактной моделью колоды.
AnyCard = WordForm | Phrase


def link(card: AnyCard) -> dict:
    """Под какой ссылкой лежит карточка: у формы и фразы свои поля."""
    return {"form": card} if isinstance(card, WordForm) else {"phrase": card}


class CardStateQuerySet(models.QuerySet):
    """Выборки состояний."""

    def for_card(self, card: AnyCard) -> "CardStateQuerySet":
        """Состояние одной карточки, какой бы таблице она ни принадлежала."""
        return self.filter(**link(card))


class GroupPostQuerySet(models.QuerySet):
    """Выборки отправленного в группу."""

    def words(self) -> "GroupPostQuerySet":
        """Только строки о словах: фразы в группу не уезжают."""
        return self.filter(form__isnull=False).select_related("form__word")

    def by_age(self) -> "GroupPostQuerySet":
        """Отправленные раньше всех — первыми: по ним колода идёт на второй круг."""
        return self.order_by("sent_at")


def unsent_words() -> models.QuerySet[WordForm]:
    """Формы слов, которые в группу ещё не уезжали.

    Обратная связь читается отсюда, а не из выборок колоды: `vocabulary` про `learning`
    не знает и знать не должен.
    """
    return WordForm.objects.filter(group_posts__isnull=True).select_related("word")
