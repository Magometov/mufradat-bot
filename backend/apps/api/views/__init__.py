"""Виды открытых ручек: по файлу на ручку."""

from apps.api.views.answers import AnswerCreateView
from apps.api.views.cards import CardListView
from apps.api.views.pictures import PhotoView, PostcardView
from apps.api.views.state import StateView
from apps.api.views.themes import ThemeListView
from apps.api.views.visits import VisitCreateView

__all__ = [
    "AnswerCreateView",
    "CardListView",
    "PhotoView",
    "PostcardView",
    "StateView",
    "ThemeListView",
    "VisitCreateView",
]
