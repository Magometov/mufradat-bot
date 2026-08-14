from django.urls import path

from apps.api.views import CardListView, ThemeListView

urlpatterns = [
    path("cards/", CardListView.as_view(), name="cards"),
    path("themes/", ThemeListView.as_view(), name="themes"),
]
