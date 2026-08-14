# Свёрнутая история колоды: девять миграций, из которых три переносили данные.
# Переносить нечего — на чистой базе таблица Entry и не появляется.

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models

CHOICES = [
    ("last_lesson", "Из последнего урока"),
    ("numbers", "Цифры"),
    ("family", "Семья"),
    ("greetings", "Знакомство"),
    ("verbs", "Глаголы"),
    ("antonyms", "Антонимы"),
    ("nouns", "Существительные"),
    ("questions", "Вопросы и предлоги"),
]


def themes_field() -> django.contrib.postgres.fields.ArrayField:
    """Поле тем: у слова и у фразы оно одно и то же."""
    return django.contrib.postgres.fields.ArrayField(
        base_field=models.CharField(choices=CHOICES, max_length=32),
        blank=True,
        default=list,
        verbose_name="Темы",
    )


class Migration(migrations.Migration):
    initial = True

    # Перечень заменённых миграций нужен базам, где они уже применены: Django сверится
    # с ним и запишет свёртку применённой, ничего не выполняя. Строки можно убрать,
    # когда свёртка запишется везде, где база живёт.
    replaces = [
        ("vocabulary", "0001_initial"),
        ("vocabulary", "0002_entry_themes"),
        ("vocabulary", "0003_entry_is_word"),
        ("vocabulary", "0004_alter_entry_themes"),
        ("vocabulary", "0005_word_wordform_phrase"),
        ("vocabulary", "0006_move_entries"),
        ("vocabulary", "0007_delete_entry"),
        ("vocabulary", "0008_images_to_cards"),
        ("vocabulary", "0009_theme_last_lesson"),
    ]

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Word",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("themes", themes_field()),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="Добавлено"
                    ),
                ),
            ],
            options={
                "verbose_name": "Слово",
                "verbose_name_plural": "Слова",
                "ordering": ("-created_at", "-id"),
            },
        ),
        migrations.CreateModel(
            name="Phrase",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("arabic", models.TextField(help_text="С огласовками", verbose_name="Арабское")),
                ("translation_ru", models.TextField(verbose_name="Перевод")),
                (
                    "transliteration",
                    models.TextField(blank=True, default="", verbose_name="Транслитерация"),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True, null=True, upload_to="cards/", verbose_name="Картинка"
                    ),
                ),
                ("themes", themes_field()),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="Добавлено"
                    ),
                ),
            ],
            options={
                "verbose_name": "Фраза",
                "verbose_name_plural": "Фразы",
                "ordering": ("-created_at", "-id"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("arabic", "translation_ru"), name="uq_phrase_arabic_translation"
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="WordForm",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("arabic", models.TextField(help_text="С огласовками", verbose_name="Арабское")),
                ("translation_ru", models.TextField(verbose_name="Перевод")),
                (
                    "transliteration",
                    models.TextField(blank=True, default="", verbose_name="Транслитерация"),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True, null=True, upload_to="cards/", verbose_name="Картинка"
                    ),
                ),
                (
                    "number",
                    models.PositiveSmallIntegerField(
                        choices=[(1, "Единственное"), (2, "Множественное")],
                        default=1,
                        verbose_name="Число",
                    ),
                ),
                (
                    "word",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="forms",
                        to="vocabulary.word",
                        verbose_name="Слово",
                    ),
                ),
            ],
            options={
                "verbose_name": "Форма",
                "verbose_name_plural": "Формы",
                "ordering": ("number",),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("word", "number"), name="uq_wordform_word_number"
                    ),
                    models.UniqueConstraint(
                        fields=("arabic", "translation_ru"), name="uq_wordform_arabic_translation"
                    ),
                ],
            },
        ),
    ]
