from django.urls import path

from apps.api.views import CardListView, ThemeListView

# Адрес `entries/` остался от единственной модели: менять его — значит выкатывать
# фронт и бэк секунда в секунду. Отдаёт он всю колоду, как и отдавал.
urlpatterns = [
    path("entries/", CardListView.as_view(), name="entries"),
    path("themes/", ThemeListView.as_view(), name="themes"),
]
