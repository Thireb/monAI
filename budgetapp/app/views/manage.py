"""The "More" page of the new UI: accounts, categories and bill reminders.

Each item opens in the edit sheet. Saving or deleting closes the sheet (``sheet_done``),
shows a toast and triggers ``manageChanged`` (the lists refresh) and ``monthChanged``
(month figures that use the item refresh too).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from budgetapp.app.forms import AccountForm, BillForm, CategoryForm
from budgetapp.models import BillReminder, Budget, Category, Tag
from budgetapp.services.month import build_month_snapshot

from .base import AppTemplateView, month_url, quick_add_context, sheet_done


@dataclass(frozen=True)
class Kind:
    """One kind of item on the page."""

    model: type[models.Model]
    form: type
    noun: str


KINDS = {
    "account": Kind(Tag, AccountForm, "account"),
    "category": Kind(Category, CategoryForm, "category"),
    "bill": Kind(BillReminder, BillForm, "bill"),
}


def get_kind(name: str) -> Kind:
    """Return the kind named in the URL, or raise 404."""
    try:
        return KINDS[name]
    except KeyError as exc:
        raise Http404("No such kind.") from exc


def lists_context(request: HttpRequest) -> dict[str, Any]:
    """The user's accounts, categories and bills."""
    user = request.user
    debt_tags = set(Tag.objects.filter(user=user, debts__isnull=False).values_list("id", flat=True))
    accounts = list(Tag.objects.filter(user=user).order_by("-is_active", "name"))
    for account in accounts:
        account.is_debt = account.id in debt_tags  # type: ignore[attr-defined]
    return {
        "accounts": accounts,
        "categories": Category.objects.filter(user=user).order_by("name"),
        "bills": BillReminder.objects.filter(user=user).order_by(
            "-is_active", "next_bill_date", "name"
        ),
    }


def delete_note(kind_name: str, item: models.Model) -> str:
    """Say what a delete also changes, for the second tap of the delete button."""
    if kind_name == "account":
        lines = item.expenses.count()  # type: ignore[attr-defined]
        transfers = item.transfers_out.count() + item.transfers_in.count()  # type: ignore
        parts = []
        if lines:
            parts.append(f"{lines} line{'s' if lines != 1 else ''} lose this account")
        if transfers:
            parts.append(f"{transfers} transfer{'s' if transfers != 1 else ''} go")
        return "Tap again: " + " and ".join(parts) if parts else "Tap again to delete"
    if kind_name == "category":
        lines = item.expenses.count()  # type: ignore[attr-defined]
        if lines:
            return f"Tap again: {lines} line{'s' if lines != 1 else ''} lose this category"
    return "Tap again to delete"


class ManageView(AppTemplateView):
    """Accounts, categories, bill reminders and links to the other pages."""

    template_name = "app/manage.html"
    nav = "more"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """The three lists, and quick add for this month."""
        context = super().get_context_data(**kwargs)
        context.update(lists_context(self.request))
        today = timezone.localdate()
        context["month_url"] = month_url(today)
        budget = Budget.objects.filter(user=self.request.user, month=today.replace(day=1)).first()
        if budget is not None:
            context["quick_add"] = quick_add_context(budget, build_month_snapshot(budget, today))
        return context


class ManagePanelView(LoginRequiredMixin, View):
    """HTMX partial: the three lists, after a change."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render the lists."""
        return render(request, "app/partials/manage_panel.html", lists_context(request))


class ItemSheetView(LoginRequiredMixin, View):
    """The edit sheet of an account, category or bill: GET shows it, POST saves it."""

    def item(self, request: HttpRequest, kind: Kind, pk: int | None) -> models.Model | None:
        """The user's item, or ``None`` for a new one."""
        if pk is None:
            return None
        return get_object_or_404(kind.model, pk=pk, user=request.user)

    def render_sheet(
        self, request: HttpRequest, kind_name: str, form: Any, item: models.Model | None
    ) -> HttpResponse:
        """Render the sheet body with ``form``."""
        is_debt = isinstance(item, Tag) and item.debts.exists()
        context = {
            "kind": kind_name,
            "noun": KINDS[kind_name].noun,
            "form": form,
            "item": item,
            "delete_note": delete_note(kind_name, item) if item else "",
            "is_debt": is_debt,
        }
        return render(request, "app/partials/manage_sheet.html", context)

    def get(self, request: HttpRequest, kind: str, pk: int | None = None) -> HttpResponse:
        """Show the form, empty or with the item."""
        config = get_kind(kind)
        item = self.item(request, config, pk)
        form = config.form(instance=item, user=request.user, prefix=kind)
        return self.render_sheet(request, kind, form, item)

    def post(self, request: HttpRequest, kind: str, pk: int | None = None) -> HttpResponse:
        """Save the item and close the sheet, or show the form with its errors."""
        config = get_kind(kind)
        item = self.item(request, config, pk)
        form = config.form(request.POST, instance=item, user=request.user, prefix=kind)
        if not form.is_valid():
            return self.render_sheet(request, kind, form, item)
        saved = form.save()
        message = f'Saved the {config.noun} "{saved.name}".'
        return sheet_done(request, message, "manageChanged", "monthChanged")


class ItemDeleteView(LoginRequiredMixin, View):
    """Delete an account, category or bill. An account that belongs to a debt stays."""

    def post(self, request: HttpRequest, kind: str, pk: int) -> HttpResponse:
        """Delete the item and close the sheet."""
        config = get_kind(kind)
        item = get_object_or_404(config.model, pk=pk, user=request.user)
        if isinstance(item, Tag) and item.debts.exists():
            message = "This account belongs to a debt. Delete the debt instead."
            return render(request, "app/partials/toast.html", {"message": message, "error": True})
        name = item.name  # type: ignore[attr-defined]
        item.delete()
        message = f'Deleted the {config.noun} "{name}".'
        return sheet_done(request, message, "manageChanged", "monthChanged")
