"""URL routes for the new UI (/app/)."""

from __future__ import annotations

from django.urls import URLPattern, path

from .views.home import HomeView
from .views.line import (
    LineCreateView,
    LineDailyToggleView,
    LineDeleteView,
    LineSheetView,
    LineSpendCreateView,
    SpendDeleteView,
)
from .views.month import MonthCreateView, MonthPanelView, MonthView
from .views.spend import SpendCreateView, SpendUndoView

app_name = "app"

urlpatterns: list[URLPattern] = [
    path("", HomeView.as_view(), name="home"),
    path("month/<int:year>/<int:month>/", MonthView.as_view(), name="month"),
    path("month/<int:year>/<int:month>/panel/", MonthPanelView.as_view(), name="month_panel"),
    path("month/<int:year>/<int:month>/create/", MonthCreateView.as_view(), name="month_create"),
    path("month/<int:year>/<int:month>/lines/", LineCreateView.as_view(), name="line_create"),
    path("lines/<int:pk>/", LineSheetView.as_view(), name="line_sheet"),
    path("lines/<int:pk>/daily/", LineDailyToggleView.as_view(), name="line_daily"),
    path("lines/<int:pk>/delete/", LineDeleteView.as_view(), name="line_delete"),
    path("lines/<int:pk>/spends/", LineSpendCreateView.as_view(), name="line_spend_create"),
    path("spends/", SpendCreateView.as_view(), name="spend_create"),
    path("spends/<int:pk>/undo/", SpendUndoView.as_view(), name="spend_undo"),
    path("spends/<int:pk>/delete/", SpendDeleteView.as_view(), name="spend_delete"),
]
