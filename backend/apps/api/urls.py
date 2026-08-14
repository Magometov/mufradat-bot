from django.urls import include, path

from apps.api.views import CardListView, ThemeListView, VisitCreateView

urlpatterns = [
    path("cards/", CardListView.as_view(), name="cards"),
    path("themes/", ThemeListView.as_view(), name="themes"),
    path("visits/", VisitCreateView.as_view(), name="visits"),
    # Только для бота: снаружи этот путь Caddy не пускает.
    path("internal/", include("apps.api.internal.urls")),
]
