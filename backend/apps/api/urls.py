from django.urls import path

from apps.api.views import EntryListView, ThemeListView

urlpatterns = [
    path("entries/", EntryListView.as_view(), name="entries"),
    path("themes/", ThemeListView.as_view(), name="themes"),
]
