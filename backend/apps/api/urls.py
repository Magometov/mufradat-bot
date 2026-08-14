from django.urls import include, path

from apps.api.views import CardListView, ThemeListView

urlpatterns = [
    path("cards/", CardListView.as_view(), name="cards"),
    path("themes/", ThemeListView.as_view(), name="themes"),
    # Только для бота: снаружи этот путь Caddy не пускает.
    path("internal/", include("apps.api.internal.urls")),
]
