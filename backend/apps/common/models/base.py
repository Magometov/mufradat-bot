from django.db import models


class BaseModel(models.Model):
    """Общее у записей, которые копятся со временем: когда появилась и порядок — свежие сверху."""

    created_at = models.DateTimeField("Создано", auto_now_add=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ("-created_at", "-id")
