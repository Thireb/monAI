"""URL routes for the new UI (/app/)."""

from __future__ import annotations

from django.urls import URLPattern, path

from .views.home import HomeView
from .views.month import (
    LineCreateView,
    LineDailyToggleView,
    MonthCreateView,
    MonthPanelView,
    MonthView,
)
from .views.spend import SpendCreateView, SpendUndoView

app_name = "app"

urlpatterns: list[URLPattern] = [
    path("", HomeView.as_view(), name="home"),
    path("month/<int:year>/<int:month>/", MonthView.as_view(), name="month"),
    path("month/<int:year>/<int:month>/panel/", MonthPanelView.as_view(), name="month_panel"),
    path("month/<int:year>/<int:month>/create/", MonthCreateView.as_view(), name="month_create"),
    path("month/<int:year>/<int:month>/lines/", LineCreateView.as_view(), name="line_create"),
    path("lines/<int:pk>/daily/", LineDailyToggleView.as_view(), name="line_daily"),
    path("spends/", SpendCreateView.as_view(), name="spend_create"),
    path("spends/<int:pk>/undo/", SpendUndoView.as_view(), name="spend_undo"),
]
