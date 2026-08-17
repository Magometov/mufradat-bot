"""Выборки состояний и то, как в них попадает карточка."""

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
