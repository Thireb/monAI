"""Line actions of the new UI: add, edit, delete, the day-to-day flag, and the line sheet.

The line sheet is a dialog that opens when the user taps a line. It shows the line's figures,
an edit form, its spends and returns for the month, and a form to add a spend or a return.
Archived months are read-only, so every change here needs a budget that is not archived.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from budgetapp.app.forms import LineForm
from budgetapp.models import Budget, Expense, SubExpense
from budgetapp.services.month import build_month_snapshot
from budgetapp.services.quick_add import QuickAddError, parse_amount, record_return, record_spend

from .base import month_date, sheet_done


def editable_line(request: HttpRequest, pk: int) -> Expense:
    """Return the user's line ``pk`` in a month that is not archived, or raise 404."""
    return get_object_or_404(
        Expense.objects.select_related("budget"),
        pk=pk,
        budget__user=request.user,
        budget__is_archived=False,
    )


def render_line_sheet(
    request: HttpRequest,
    line: Expense,
    form: LineForm | None = None,
    message: str = "",
    spend_error: str = "",
    edit_open: bool = False,
) -> HttpResponse:
    """Render the body of the line sheet for ``line``."""
    snap = build_month_snapshot(line.budget, timezone.localdate())
    line_view = next((item for item in snap.lines if item.id == line.id), None)
    context: dict[str, Any] = {
        "line": line,
        "line_view": line_view,
        "budget": line.budget,
        "form": form or LineForm(instance=line, user=request.user, prefix="edit"),
        "spends": line.sub_expenses.order_by("-created_at", "-id"),
        "message": message,
        "spend_error": spend_error,
        "edit_open": edit_open or bool(form and form.errors),
    }
    return render(request, "app/partials/line_sheet.html", context)


class LineCreateView(LoginRequiredMixin, View):
    """Add an expense line to a month (HTMX form on the month page)."""

    def post(self, request: HttpRequest, year: int, month: int) -> HttpResponse:
        """Save the line, or return the form with its errors."""
        budget = get_object_or_404(
            Budget, user=request.user, month=month_date(year, month), is_archived=False
        )
        form = LineForm(request.POST, user=request.user, prefix="line")
        if not form.is_valid():
            return render(
                request,
                "app/partials/line_form.html",
                {"line_form": form, "budget": budget},
            )
        line = form.save(commit=False)
        line.budget = budget
        line.save()
        response = render(
            request,
            "app/partials/line_form.html",
            {
                "line_form": LineForm(user=request.user, prefix="line"),
                "budget": budget,
                "saved_name": line.name,
            },
        )
        response["HX-Trigger"] = "monthChanged"
        return response


class LineDailyToggleView(LoginRequiredMixin, View):
    """Mark or unmark a line as day-to-day spending."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Flip ``is_daily`` and ask the page to refresh its panel."""
        line = editable_line(request, pk)
        line.is_daily = not line.is_daily
        line.save(update_fields=["is_daily", "updated_at"])
        response = HttpResponse(status=204)
        response["HX-Trigger"] = "monthChanged"
        return response


class LineSheetView(LoginRequiredMixin, View):
    """Show the line sheet (GET) or save the edit form in it (POST)."""

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Render the sheet for the line."""
        return render_line_sheet(request, editable_line(request, pk))

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Save the edited line. Form errors come back with status 200, so HTMX shows them."""
        line = editable_line(request, pk)
        form = LineForm(request.POST, instance=line, user=request.user, prefix="edit")
        if not form.is_valid():
            return render_line_sheet(request, line, form=form)
        line = form.save()
        response = render_line_sheet(request, line, message="Saved.", edit_open=True)
        response["HX-Trigger"] = "monthChanged"
        return response


class LineDeleteView(LoginRequiredMixin, View):
    """Delete a line and its spends. The sheet asks for a second tap first."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Delete the line, close the sheet and show a toast."""
        line = editable_line(request, pk)
        name = line.name
        line.delete()
        return sheet_done(request, f'Deleted the line "{name}".', "monthChanged")


class LineSpendCreateView(LoginRequiredMixin, View):
    """Add a spend or a return to a line from the line sheet."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Save the spend or return, then render the sheet again."""
        line = editable_line(request, pk)
        note = request.POST.get("note", "").strip()
        try:
            amount = parse_amount(request.POST.get("amount", ""))
        except QuickAddError as exc:
            return render_line_sheet(request, line, spend_error=str(exc))
        if request.POST.get("kind") == "return":
            record_return(line, amount, note)
            message = "Return saved."
        else:
            record_spend(line, amount, note)
            message = "Spend saved."
        response = render_line_sheet(request, line, message=message)
        response["HX-Trigger"] = "monthChanged"
        return response


class SpendDeleteView(LoginRequiredMixin, View):
    """Delete one spend or return from the line sheet. The sheet asks for a second tap first."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Delete the spend, then render the sheet of its line again."""
        spend = get_object_or_404(
            SubExpense.objects.select_related("expense__budget"),
            pk=pk,
            expense__budget__user=request.user,
            expense__budget__is_archived=False,
        )
        line = spend.expense
        kind = "return" if spend.is_return else "spend"
        spend.delete()
        response = render_line_sheet(request, line, message=f"Deleted the {kind}.")
        response["HX-Trigger"] = "monthChanged"
        return response
