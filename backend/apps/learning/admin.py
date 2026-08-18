"""Состояния карточек и отправленное в группу: только смотреть."""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.learning.models import CardState, GroupPost


@admin.register(CardState)
class CardStateAdmin(admin.ModelAdmin):
    list_display = ("learner", "card", "level", "step", "lapses", "due_at", "reminded_at")
    list_filter = ("level", "lapses", "due_at")
    search_fields = ("learner__username", "form__arabic", "phrase__arabic")
    date_hierarchy = "due_at"

    def get_queryset(self, request: HttpRequest) -> QuerySet[CardState]:
        """Человек и карточка нужны в каждой строке списка."""
        return super().get_queryset(request).select_related("learner", "form", "phrase")

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Состояния пишет приложение."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: CardState | None = None) -> bool:
        """Уровни правит только оценка, иначе расписание разъедется."""
        return False

    @admin.display(description="Карточка")
    def card(self, obj: CardState) -> str:
        return str(obj.card)


@admin.register(GroupPost)
class GroupPostAdmin(admin.ModelAdmin):
    """Что уже уезжало в группу. Удаление оставлено: снести строки — начать круг заново."""

    list_display = ("word", "sent_at")
    date_hierarchy = "sent_at"
    search_fields = ("form__arabic", "form__translation_ru")

    def get_queryset(self, request: HttpRequest) -> QuerySet[GroupPost]:
        """Слово нужно в каждой строке списка."""
        return super().get_queryset(request).words()

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Записи заводит рассылка."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: GroupPost | None = None) -> bool:
        """Время отправки правит рассылка, иначе круг колоды разъедется."""
        return False

    @admin.display(description="Слово")
    def word(self, obj: GroupPost) -> str:
        return str(obj.card)
