"""Month settings of the new UI: income and currency, transfers, the PDF email and delete.

These forms sit in the "Month settings" card under the month panel. Each change answers with
the card again and triggers ``monthChanged``, so the month figures refresh too.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import View

from budgetapp.app.forms import IncomeForm, TransferForm
from budgetapp.models import Budget, IncomeHistory, TagTransfer
from budgetapp.services.report import send_report
from budgetapp.templatetags.app_format import money

from .base import month_date
from .goals import toast


def editable_budget(request: HttpRequest, year: int, month: int) -> Budget:
    """The user's budget of ``year``/``month`` that is not archived, or raise 404."""
    return get_object_or_404(
        Budget, user=request.user, month=month_date(year, month), is_archived=False
    )


def settings_context(
    request: HttpRequest,
    budget: Budget,
    income_form: IncomeForm | None = None,
    transfer_form: TransferForm | None = None,
    message: str = "",
) -> dict[str, Any]:
    """Context of the month settings card."""
    return {
        "budget": budget,
        "income_form": income_form or IncomeForm(instance=budget, prefix="income"),
        "transfer_form": transfer_form or TransferForm(user=request.user, prefix="transfer"),
        "transfers": budget.tag_transfers.select_related("from_tag", "to_tag"),
        "settings_message": message,
    }


def render_settings(request: HttpRequest, budget: Budget, changed: bool, **kwargs: Any) -> Any:
    """Render the card; after a change, also refresh the month figures."""
    response = render(
        request, "app/partials/month_settings.html", settings_context(request, budget, **kwargs)
    )
    if changed:
        response["HX-Trigger"] = "monthChanged"
    return response


class IncomeUpdateView(LoginRequiredMixin, View):
    """Change the month's income and currency, and keep the old values in IncomeHistory."""

    def post(self, request: HttpRequest, year: int, month: int) -> HttpResponse:
        """Save the income, or show the form errors."""
        budget = editable_budget(request, year, month)
        old_income, old_currency = budget.income, budget.currency
        form = IncomeForm(request.POST, instance=budget, prefix="income")
        if not form.is_valid():
            return render_settings(request, budget, False, income_form=form)
        budget = form.save()
        if (budget.income, budget.currency) != (old_income, old_currency):
            IncomeHistory.objects.create(
                budget=budget,
                old_amount=old_income,
                new_amount=budget.income,
                old_currency=old_currency,
                new_currency=budget.currency,
            )
        message = f"Income saved: {budget.currency} {money(budget.income)}."
        return render_settings(request, budget, True, message=message)


class TransferCreateView(LoginRequiredMixin, View):
    """Move money from one account to another in this month."""

    def post(self, request: HttpRequest, year: int, month: int) -> HttpResponse:
        """Save the transfer, or show the form errors."""
        budget = editable_budget(request, year, month)
        form = TransferForm(
            request.POST,
            instance=TagTransfer(budget=budget),
            user=request.user,
            prefix="transfer",
        )
        if not form.is_valid():
            return render_settings(request, budget, False, transfer_form=form)
        transfer = form.save()
        message = f"Moved {money(transfer.amount)} from {transfer.from_tag} to {transfer.to_tag}."
        return render_settings(request, budget, True, message=message)


class TransferDeleteView(LoginRequiredMixin, View):
    """Delete a transfer."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Delete it and render the card again."""
        transfer = get_object_or_404(
            TagTransfer, pk=pk, budget__user=request.user, budget__is_archived=False
        )
        budget = transfer.budget
        transfer.delete()
        return render_settings(request, budget, True, message="Deleted the transfer.")


class MonthEmailView(LoginRequiredMixin, View):
    """Email the month's PDF report; answer with a toast."""

    def post(self, request: HttpRequest, year: int, month: int) -> HttpResponse:
        """Send the report and show the result."""
        result = send_report(request.user, editable_budget(request, year, month))
        return toast(request, result.message, error=not result.ok)


class MonthDeleteView(LoginRequiredMixin, View):
    """Delete the month with its lines and spends, then open the year page."""

    def post(self, request: HttpRequest, year: int, month: int) -> HttpResponse:
        """Delete the budget and send the browser to the months page."""
        budget = get_object_or_404(Budget, user=request.user, month=month_date(year, month))
        budget.delete()
        response = HttpResponse(status=204)
        response["HX-Redirect"] = f"{reverse('app:months')}?year={year}"
        return response
