"""Картинки карточек: в колоде они лежат только в webp."""

from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile, File
from PIL import Image, ImageOps

# Потолок по длинной стороне. Модель рисует ровно столько, так что нужен он не ей, а
# ручной загрузке через админку: карточка показывает картинку вчетверо мельче.
SIDE = 1024

QUALITY = 82

# Каждый файл жмётся один раз за свою жизнь, поэтому берём самый плотный режим.
METHOD = 6


def _has_alpha(picture: Image.Image) -> bool:
    """Есть ли у картинки прозрачность: без неё лишний канал только весит."""
    return picture.mode in ("RGBA", "LA") or "transparency" in picture.info


def to_webp(image: File) -> ContentFile:
    """Пережимает картинку в webp. Имя — прежнее, расширение новое."""
    source = Image.open(image)
    # Снимок с телефона приезжает боком: поворот лежит в EXIF, а webp его не хранит.
    picture = ImageOps.exif_transpose(source)
    picture = picture.convert("RGBA" if _has_alpha(picture) else "RGB")
    # thumbnail только уменьшает: картинке от модели он ничего не делает.
    picture.thumbnail((SIDE, SIDE))

    buffer = BytesIO()
    picture.save(buffer, format="WEBP", quality=QUALITY, method=METHOD)

    return ContentFile(buffer.getvalue(), name=f"{Path(image.name or 'card').stem}.webp")
