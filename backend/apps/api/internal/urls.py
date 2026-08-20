from django.urls import path

from apps.api.internal.views import (
    FormCreateView,
    GroupCardView,
    KnownView,
    LessonMoveView,
    LessonView,
    PhraseCreateView,
    ProgressResetView,
    ProgressView,
    RemindersSwitchView,
    ReminderTakeView,
    SearchView,
)

urlpatterns = [
    path("forms/", FormCreateView.as_view(), name="bot-forms"),
    path("phrases/", PhraseCreateView.as_view(), name="bot-phrases"),
    path("known/", KnownView.as_view(), name="bot-known"),
    path("lesson/", LessonView.as_view(), name="bot-lesson"),
    path("lesson/move/", LessonMoveView.as_view(), name="bot-lesson-move"),
    path("group/take/", GroupCardView.as_view(), name="bot-group"),
    path("search/", SearchView.as_view(), name="bot-search"),
    path("reminders/take/", ReminderTakeView.as_view(), name="bot-reminders"),
    path("reminders/switch/", RemindersSwitchView.as_view(), name="bot-reminders-switch"),
    path("progress/", ProgressView.as_view(), name="bot-progress"),
    path("progress/reset/", ProgressResetView.as_view(), name="bot-progress-reset"),
]
