from django.urls import include, path

from apps.api.views import (
    AnswerCreateView,
    CardListView,
    StateView,
    ThemeListView,
    VisitCreateView,
)

urlpatterns = [
    path("cards/", CardListView.as_view(), name="cards"),
    path("themes/", ThemeListView.as_view(), name="themes"),
    path("state/", StateView.as_view(), name="state"),
    path("answers/", AnswerCreateView.as_view(), name="answers"),
    path("visits/", VisitCreateView.as_view(), name="visits"),
    # Только для бота: снаружи этот путь Caddy не пускает.
    path("internal/", include("apps.api.internal.urls")),
]
