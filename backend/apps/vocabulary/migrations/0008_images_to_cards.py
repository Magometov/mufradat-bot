from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.models import Value
from django.db.models.functions import Replace

OLD = "entries/"
NEW = "cards/"


def rename(apps: Apps, old: str, new: str) -> None:
    """Переписывает начало пути к картинке у обеих таблиц одним UPDATE на каждую.

    Сами файлы миграция не двигает — доступа к тому у неё нет. Их переносят руками,
    и порядок такой: сначала файлы, потом миграция. Иначе картинки не найдутся.
    """
    for name in ("WordForm", "Phrase"):
        apps.get_model("vocabulary", name).objects.filter(image__startswith=old).update(
            image=Replace("image", Value(old), Value(new))
        )


def to_cards(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    rename(apps, OLD, NEW)


def to_entries(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    rename(apps, NEW, OLD)


class Migration(migrations.Migration):
    dependencies = [
        ("vocabulary", "0007_delete_entry"),
    ]

    operations = [
        migrations.AlterField(
            model_name="phrase",
            name="image",
            field=models.ImageField(
                blank=True, null=True, upload_to="cards/", verbose_name="Картинка"
            ),
        ),
        migrations.AlterField(
            model_name="wordform",
            name="image",
            field=models.ImageField(
                blank=True, null=True, upload_to="cards/", verbose_name="Картинка"
            ),
        ),
        migrations.RunPython(to_cards, to_entries),
    ]
