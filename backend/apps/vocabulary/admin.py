from django import forms
from django.contrib import admin
from django.db.models import Q, QuerySet
from django.http import HttpRequest

from apps.vocabulary.models import Entry
from apps.vocabulary.themes import Theme


class HasImageFilter(admin.SimpleListFilter):
    """Фильтр «картинка есть / картинки нет»."""

    title = "Картинка"
    parameter_name = "has_image"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        return [("yes", "Есть"), ("no", "Нет")]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Entry]) -> QuerySet[Entry]:
        empty = Q(image="") | Q(image__isnull=True)
        if self.value() == "yes":
            return queryset.exclude(empty)
        if self.value() == "no":
            return queryset.filter(empty)
        return queryset


class ThemeFilter(admin.SimpleListFilter):
    """Фильтр по теме, плюс отдельный пункт для карточек без тем."""

    title = "Тема"
    parameter_name = "theme"
    NONE = "none"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        return [*Theme.choices, (self.NONE, "Без темы")]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Entry]) -> QuerySet[Entry]:
        value = self.value()
        if value is None:
            return queryset
        if value == self.NONE:
            return queryset.filter(themes=[])
        return queryset.filter(themes__contains=[value])


class EntryForm(forms.ModelForm):
    """Темы — чекбоксы: по умолчанию массив правился бы строкой через запятую."""

    themes = forms.MultipleChoiceField(
        label="Темы",
        choices=Theme.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Entry
        fields = "__all__"


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    form = EntryForm
    list_display = ("arabic", "translation_ru", "is_word", "theme_names", "has_image", "created_at")
    list_filter = ("is_word", ThemeFilter, HasImageFilter)
    search_fields = ("translation_ru", "transliteration")
    readonly_fields = ("created_at",)
    actions = ("mark_as_words", "mark_as_phrases")
    fieldsets = (
        (None, {"fields": ("arabic", "translation_ru", "transliteration", "is_word")}),
        ("Темы", {"fields": ("themes",)}),
        ("Картинка", {"fields": ("image",)}),
        ("Служебное", {"fields": ("created_at",)}),
    )

    @admin.action(description="Отметить как слова")
    def mark_as_words(self, request: HttpRequest, queryset: QuerySet[Entry]) -> None:
        self._mark(request, queryset, is_word=True)

    @admin.action(description="Отметить как фразы")
    def mark_as_phrases(self, request: HttpRequest, queryset: QuerySet[Entry]) -> None:
        self._mark(request, queryset, is_word=False)

    def _mark(self, request: HttpRequest, queryset: QuerySet[Entry], *, is_word: bool) -> None:
        changed = queryset.update(is_word=is_word)
        self.message_user(request, f"Отмечено {'словом' if is_word else 'фразой'}: {changed}")

    @admin.display(boolean=True, description="Картинка")
    def has_image(self, obj: Entry) -> bool:
        return bool(obj.image)

    @admin.display(description="Темы")
    def theme_names(self, obj: Entry) -> str:
        labels = dict(Theme.choices)
        return ", ".join(labels.get(slug, slug) for slug in obj.themes) or "—"
