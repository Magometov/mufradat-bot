"""Картинки для Telegram. Обычные виды Django, не DRF: тут не разговор, а файл."""

from django.core.files.base import File
from django.http import FileResponse, Http404, HttpRequest
from django.views import View

from apps.vocabulary.models import Phrase, WordForm
from apps.vocabulary.services import cards_by_id, photo, postcard

# Столько картинку разрешено держать в кэше. Не «навсегда»: адрес не меняется, а
# содержимое поменяется, если карточку поправить в админке.
CACHE = "public, max-age=3600"


class PictureView(View):
    """Общее: найти карточку по номеру и отдать готовый файл."""

    def take(self, card: WordForm | Phrase) -> File | None:
        raise NotImplementedError

    def get(self, request: HttpRequest, card_id: str) -> FileResponse:
        card = cards_by_id([card_id]).get(card_id)
        ready = self.take(card) if card is not None else None

        if ready is None:
            raise Http404

        return FileResponse(ready, content_type="image/jpeg", headers={"Cache-Control": CACHE})


class PostcardView(PictureView):
    """Собранная карточка: слово, перевод, иллюстрация и транслитерация одной картинкой."""

    def take(self, card: WordForm | Phrase) -> File | None:
        return postcard(card)


class PhotoView(PictureView):
    """Голая иллюстрация джипегом: её прячет спойлер в напоминаниях."""

    def take(self, card: WordForm | Phrase) -> File | None:
        return photo(card)
