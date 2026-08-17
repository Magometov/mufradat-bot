"""Журнал входов начинает ссылаться на человека.

Связь добавляется до переноса, старые поля снимаются после: иначе переносить нечего.
"""

import django.db.models.deletion
from django.db import migrations, models


def fill_learners(apps, schema_editor):
    """Заводит человека на каждый Telegram id и проставляет связь. Ник — из свежего захода."""
    Visit = apps.get_model("common", "Visit")
    Learner = apps.get_model("common", "Learner")
    known = {}

    for visit in Visit.objects.filter(telegram_id__isnull=False).order_by("created_at", "id"):
        learner = known.get(visit.telegram_id)

        if learner is None:
            learner = Learner.objects.create(
                telegram_id=visit.telegram_id,
                username=visit.username,
            )
            known[visit.telegram_id] = learner
        elif visit.username and learner.username != visit.username:
            learner.username = visit.username
            learner.save(update_fields=["username"])

        visit.learner = learner
        visit.save(update_fields=["learner"])


def unfill_learners(apps, schema_editor):
    """Возвращает id и ник в журнал."""
    Visit = apps.get_model("common", "Visit")

    for visit in Visit.objects.select_related("learner").filter(learner__isnull=False):
        visit.telegram_id = visit.learner.telegram_id
        visit.username = visit.learner.username
        visit.save(update_fields=["telegram_id", "username"])


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0002_learner"),
    ]

    operations = [
        migrations.AddField(
            model_name="visit",
            name="learner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="visits",
                to="common.learner",
                verbose_name="Человек",
            ),
        ),
        migrations.RunPython(fill_learners, unfill_learners),
        migrations.RemoveField(model_name="visit", name="telegram_id"),
        migrations.RemoveField(model_name="visit", name="username"),
    ]
