from django.urls import path

from apps.api.views import EntryListView

urlpatterns = [
    path("entries/", EntryListView.as_view(), name="entries"),
]
