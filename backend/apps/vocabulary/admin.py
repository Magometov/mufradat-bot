from django import forms
from django.contrib import admin
from django.db import transaction
from django.db.models import Q, QuerySet
from django.http import HttpRequest

from apps.vocabulary.models import Number, Phrase, Word, WordForm
from apps.vocabulary.themes import Theme


class HasImageFilter(admin.SimpleListFilter):
    """Фильтр «картинка есть / картинки нет»; `path` говорит, где лежит поле."""

    title = "Картинка"
    parameter_name = "has_image"
    path = "image"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        return [("yes", "Есть"), ("no", "Нет")]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        empty = Q(**{self.path: ""}) | Q(**{f"{self.path}__isnull": True})
        if self.value() == "yes":
            return queryset.exclude(empty)
        if self.value() == "no":
            return queryset.filter(empty).distinct()
        return queryset


class WordHasImageFilter(HasImageFilter):
    """У слова форм две, поэтому «нет» — это «хотя бы одна форма без картинки»."""

    path = "forms__image"


class ThemeFilter(admin.SimpleListFilter):
    """Фильтр по теме, плюс отдельный пункт для карточек без тем."""

    title = "Тема"
    parameter_name = "theme"
    NONE = "none"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        return [*Theme.choices, (self.NONE, "Без темы")]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        value = self.value()
        if value is None:
            return queryset
        if value == self.NONE:
            return queryset.filter(themes=[])
        return queryset.filter(themes__contains=[value])


class ThemesForm(forms.ModelForm):
    """Темы — чекбоксы: по умолчанию массив правился бы строкой через запятую.

    Модель не названа: форма одна на слово и на фразу, подставляет её админка.
    """

    themes = forms.MultipleChoiceField(
        label="Темы",
        choices=Theme.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class WordFormInline(admin.TabularInline):
    """Написания слова: единственное и множественное число."""

    model = WordForm
    extra = 0
    max_num = len(Number.choices)
    fields = ("number", "arabic", "translation_ru", "transliteration", "image")


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    form = ThemesForm
    inlines = (WordFormInline,)
    list_display = ("title", "form_names", "theme_names", "has_image", "created_at")
    list_filter = (ThemeFilter, WordHasImageFilter)
    search_fields = ("forms__translation_ru", "forms__transliteration")
    readonly_fields = ("created_at",)
    actions = ("to_phrases",)
    fieldsets = (
        ("Темы", {"fields": ("themes",)}),
        ("Служебное", {"fields": ("created_at",)}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Word]:
        # Каждая колонка списка ходит по формам: без prefetch страница даёт запрос
        # на строку.
        return super().get_queryset(request).prefetch_related("forms")

    @admin.display(description="Слово")
    def title(self, obj: Word) -> str:
        return str(obj)

    @admin.display(description="Формы")
    def form_names(self, obj: Word) -> str:
        labels = dict(Number.choices)
        return ", ".join(labels[form.number] for form in obj.forms.all()) or "—"

    @admin.display(description="Темы")
    def theme_names(self, obj: Word) -> str:
        return _theme_names(obj.themes)

    @admin.display(boolean=True, description="Картинка")
    def has_image(self, obj: Word) -> bool:
        forms = list(obj.forms.all())
        return bool(forms) and all(form.image for form in forms)

    @admin.action(description="Перенести во фразы")
    def to_phrases(self, request: HttpRequest, queryset: QuerySet[Word]) -> None:
        """Слово с двумя формами фразой быть не может — такие пропускаются."""
        moved = 0
        skipped: list[str] = []

        for word in queryset.prefetch_related("forms"):
            forms = list(word.forms.all())
            if len(forms) != 1:
                skipped.append(str(word))
                continue

            _to_phrase(word, forms[0])
            moved += 1

        self.message_user(request, f"Перенесено во фразы: {moved}")
        if skipped:
            self.message_user(
                request,
                "Пропущены слова с двумя формами: " + ", ".join(skipped),
                level="warning",
            )


@admin.register(Phrase)
class PhraseAdmin(admin.ModelAdmin):
    form = ThemesForm
    list_display = ("arabic", "translation_ru", "theme_names", "has_image", "created_at")
    list_filter = (ThemeFilter, HasImageFilter)
    search_fields = ("translation_ru", "transliteration")
    readonly_fields = ("created_at",)
    actions = ("to_words",)
    fieldsets = (
        (None, {"fields": ("arabic", "translation_ru", "transliteration")}),
        ("Темы", {"fields": ("themes",)}),
        ("Картинка", {"fields": ("image",)}),
        ("Служебное", {"fields": ("created_at",)}),
    )

    @admin.display(description="Темы")
    def theme_names(self, obj: Phrase) -> str:
        return _theme_names(obj.themes)

    @admin.display(boolean=True, description="Картинка")
    def has_image(self, obj: Phrase) -> bool:
        return bool(obj.image)

    @admin.action(description="Перенести в слова")
    def to_words(self, request: HttpRequest, queryset: QuerySet[Phrase]) -> None:
        moved = sum(_to_word(phrase) for phrase in queryset)
        self.message_user(request, f"Перенесено в слова: {moved}")


def _theme_names(themes: list[str]) -> str:
    labels = dict(Theme.choices)
    return ", ".join(labels.get(slug, slug) for slug in themes) or "—"


@transaction.atomic
def _to_phrase(word: Word, form: WordForm) -> None:
    """Переносит слово во фразы вместе с датой и файлом картинки.

    Файл остаётся на месте: удаление строки его не трогает, а путь переезжает как
    есть. Дата проставляется вторым запросом — `auto_now_add` чужую не принимает,
    а без неё перенесённая карточка прыгнула бы в начало колоды.
    """
    phrase = Phrase.objects.create(
        themes=word.themes,
        arabic=form.arabic,
        translation_ru=form.translation_ru,
        transliteration=form.transliteration,
        image=form.image.name,
    )
    Phrase.objects.filter(pk=phrase.pk).update(created_at=word.created_at)
    word.delete()


@transaction.atomic
def _to_word(phrase: Phrase) -> bool:
    """Переносит фразу в слова единственным числом; дата и файл сохраняются."""
    word = Word.objects.create(themes=phrase.themes)
    Word.objects.filter(pk=word.pk).update(created_at=phrase.created_at)
    WordForm.objects.create(
        word=word,
        number=Number.SINGULAR,
        arabic=phrase.arabic,
        translation_ru=phrase.translation_ru,
        transliteration=phrase.transliteration,
        image=phrase.image.name,
    )
    phrase.delete()

    return True
