"""Quick add (record a spend) and undo, for the new UI's quick-add sheet."""

from __future__ import annotations

import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from budgetapp.models import Budget, Expense, SubExpense
from budgetapp.services.month import build_month_snapshot
from budgetapp.services.quick_add import (
    QuickAddError,
    match_lines,
    parse_amount,
    parse_spend_text,
    record_spend,
)

# How long the "Added!" card (and its Undo button) stays, in milliseconds.
UNDO_WINDOW_MS = 8000


def _result(
    request: HttpRequest, message: str, choices: list[Expense] | None = None, amount: str = ""
) -> HttpResponse:
    """Render a message (and optional line choices) inside the quick-add sheet."""
    return render(
        request,
        "app/partials/quick_add_result.html",
        {"message": message, "choices": choices or [], "amount": amount},
    )


class SpendCreateView(LoginRequiredMixin, View):
    """Record a spend from the amount + line fields, or from the typed text."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Save the spend and answer with the "Added!" card, or explain what is missing."""
        budget = get_object_or_404(
            Budget, pk=request.POST.get("budget"), user=request.user, is_archived=False
        )
        text = request.POST.get("text", "").strip()
        note = request.POST.get("note", "").strip()
        try:
            if text:
                parsed = parse_spend_text(text)
                amount = parsed.amount
                matches = match_lines(budget, parsed.words, parsed.account)
                if not matches:
                    return _result(
                        request, f'No line matches "{parsed.words or text}". Pick a line above.'
                    )
                if len(matches) > 1:
                    return _result(request, "Which line?", matches, f"{amount}")
                line = matches[0]
            else:
                amount = parse_amount(request.POST.get("amount", ""))
                line_id = request.POST.get("line")
                if not line_id:
                    return _result(request, "Pick a line for this spend.")
                line = get_object_or_404(Expense, pk=line_id, budget=budget)
        except QuickAddError as exc:
            return _result(request, str(exc))

        spend = record_spend(line, amount, note)
        snap = build_month_snapshot(budget, timezone.localdate())
        line_view = next((item for item in snap.lines if item.id == line.id), None)
        response = render(
            request,
            "app/partials/spend_added.html",
            {
                "spend": spend,
                "line": line_view,
                "snap": snap,
                "budget": budget,
                "undo_ms": UNDO_WINDOW_MS,
            },
        )
        response["HX-Trigger"] = json.dumps({"monthChanged": True, "spendAdded": True})
        return response


class SpendUndoView(LoginRequiredMixin, View):
    """Delete a spend that was just added (the Undo button on the "Added!" card)."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Delete the spend and replace the card with a short note."""
        spend = get_object_or_404(
            SubExpense,
            pk=pk,
            expense__budget__user=request.user,
            expense__budget__is_archived=False,
        )
        name = spend.expense.name
        spend.delete()
        response = render(request, "app/partials/spend_undone.html", {"line_name": name})
        response["HX-Trigger"] = "monthChanged"
        return response
