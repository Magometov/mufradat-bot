import django.contrib.postgres.fields
from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.models import Func, Value

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

GONE = "dialog3"


class ArrayRemove(Func):
    """`array_remove` из postgres: своей функции у Django для этого нет."""

    function = "array_remove"


def drop_gone(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Вычищает снятую тему из массивов — одним UPDATE на таблицу.

    Убрать её только из перечисления мало: строка осталась бы лежать в базе, а первая
    же правка карточки в админке стёрла бы её тихо и вразнобой. Обратного хода нет —
    кто её носил, после этого не восстановить.
    """
    for name in ("Word", "Phrase"):
        apps.get_model("vocabulary", name).objects.filter(themes__contains=[GONE]).update(
            themes=ArrayRemove("themes", Value(GONE, output_field=models.CharField(max_length=32)))
        )


def themes_field() -> django.contrib.postgres.fields.ArrayField:
    """Поле тем: у слова и у фразы оно одно и то же."""
    return django.contrib.postgres.fields.ArrayField(
        base_field=models.CharField(choices=CHOICES, max_length=32),
        blank=True,
        default=list,
        verbose_name="Темы",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("vocabulary", "0008_images_to_cards"),
    ]

    operations = [
        migrations.AlterField(model_name="phrase", name="themes", field=themes_field()),
        migrations.AlterField(model_name="word", name="themes", field=themes_field()),
        migrations.RunPython(drop_gone, migrations.RunPython.noop),
    ]
