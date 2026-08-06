from django.contrib import admin

from apps.vocabulary.models import Entry


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("arabic", "translation_ru", "has_image", "created_at")
    search_fields = ("translation_ru", "transliteration")
    readonly_fields = ("created_at",)
    fieldsets = (
        (None, {"fields": ("arabic", "translation_ru", "transliteration")}),
        ("Картинка", {"fields": ("image",)}),
        ("Служебное", {"fields": ("created_at",)}),
    )

    @admin.display(boolean=True, description="Картинка")
    def has_image(self, obj: Entry) -> bool:
        return bool(obj.image)
