from django.urls import path

from apps.api.internal.views import (
    FormCreateView,
    LessonMoveView,
    LessonView,
    PhraseCreateView,
    ProgressResetView,
    ProgressView,
    RemindersSwitchView,
    ReminderTakeView,
)

urlpatterns = [
    path("forms/", FormCreateView.as_view(), name="bot-forms"),
    path("phrases/", PhraseCreateView.as_view(), name="bot-phrases"),
    path("lesson/", LessonView.as_view(), name="bot-lesson"),
    path("lesson/move/", LessonMoveView.as_view(), name="bot-lesson-move"),
    path("reminders/take/", ReminderTakeView.as_view(), name="bot-reminders"),
    path("reminders/switch/", RemindersSwitchView.as_view(), name="bot-reminders-switch"),
    path("progress/", ProgressView.as_view(), name="bot-progress"),
    path("progress/reset/", ProgressResetView.as_view(), name="bot-progress-reset"),
]
