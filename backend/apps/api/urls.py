from django.urls import include, path

from apps.api.views import (
    AnswerCreateView,
    CardListView,
    PhotoView,
    PostcardView,
    StateView,
    ThemeListView,
    VisitCreateView,
)

urlpatterns = [
    path("cards/", CardListView.as_view(), name="cards"),
    # Картинки для Telegram: он скачивает их сам, поэтому адреса открытые.
    path("card/<str:card_id>.jpg", PostcardView.as_view(), name="postcard"),
    path("photo/<str:card_id>.jpg", PhotoView.as_view(), name="photo"),
    path("themes/", ThemeListView.as_view(), name="themes"),
    path("state/", StateView.as_view(), name="state"),
    path("answers/", AnswerCreateView.as_view(), name="answers"),
    path("visits/", VisitCreateView.as_view(), name="visits"),
    # Только для бота: снаружи этот путь Caddy не пускает.
    path("internal/", include("apps.api.internal.urls")),
]
