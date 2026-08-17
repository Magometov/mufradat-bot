from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.common.models import BaseModel
from apps.vocabulary.constants import Number, Theme
from apps.vocabulary.models.base import Card


class Word(BaseModel):
    """Слово — понятие; написания лежат в `WordForm`, раздел один на все формы."""

    themes = ArrayField(
        models.CharField(max_length=32, choices=Theme.choices),
        verbose_name="Темы",
        default=list,
        blank=True,
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Слово"
        verbose_name_plural = "Слова"

    def __str__(self) -> str:
        form = self.singular or self.forms.first()

        return str(form) if form else f"слово без форм (№{self.pk})"

    @property
    def singular(self) -> "WordForm | None":
        """Форма единственного числа; идёт по `forms.all()`, чтобы работал prefetch."""
        return next((form for form in self.forms.all() if form.number == Number.SINGULAR), None)


class WordForm(Card):
    """Написание слова в одном числе. У каждого числа своя картинка."""

    word = models.ForeignKey(
        Word,
        verbose_name="Слово",
        related_name="forms",
        on_delete=models.CASCADE,
    )
    number = models.PositiveSmallIntegerField(
        "Число",
        choices=Number.choices,
        default=Number.SINGULAR,
    )

    class Meta:
        verbose_name = "Форма"
        verbose_name_plural = "Формы"
        ordering = ("number",)
        constraints = [
            models.UniqueConstraint(
                fields=["word", "number"],
                name="uq_wordform_word_number",
            ),
            models.UniqueConstraint(
                fields=["arabic", "translation_ru"],
                name="uq_wordform_arabic_translation",
            ),
        ]

    @property
    def themes(self) -> list[str]:
        """Разделы у формы те же, что у слова: раздел — свойство понятия."""
        return self.word.themes
