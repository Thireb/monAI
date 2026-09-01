"""Tag transfer create/delete views (zero-sum account moves)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from budgetapp.models import Budget, Tag, TagTransfer

from .base import LoginRequiredView


class TagTransferCreateView(LoginRequiredView):
    """Create a tag-to-tag transfer within a budget month."""

    def _format_currency(self, val: float) -> str:
        return intcomma(f"{val:,.2f}")

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(
            Budget, month=budget_date, is_archived=False, user=request.user
        )

        from_tag_id = request.POST.get("from_tag")
        to_tag_id = request.POST.get("to_tag")
        amount_raw = request.POST.get("amount", "").strip()
        note = (request.POST.get("note") or "").strip()[:255]

        if not from_tag_id or not to_tag_id:
            return JsonResponse(
                {"status": "error", "message": "Select both accounts."},
                status=400,
            )
        try:
            amount = Decimal(amount_raw)
        except (InvalidOperation, TypeError):
            return JsonResponse(
                {"status": "error", "message": "Enter a valid amount."},
                status=400,
            )

        from_tag = get_object_or_404(Tag, id=from_tag_id, user=request.user)
        to_tag = get_object_or_404(Tag, id=to_tag_id, user=request.user)

        try:
            transfer = TagTransfer(
                budget=budget,
                from_tag=from_tag,
                to_tag=to_tag,
                amount=amount,
                note=note,
            )
            transfer.save()
        except ValidationError as exc:
            if hasattr(exc, "message_dict") and exc.message_dict:
                msg = "; ".join(
                    e for errs in exc.message_dict.values() for e in errs
                )
            else:
                msg = "; ".join(exc.messages)
            return JsonResponse({"status": "error", "message": msg}, status=400)

        return JsonResponse(
            {
                "status": "success",
                "message": "Transfer recorded.",
                "transfer": {
                    "id": transfer.id,
                    "from_tag": from_tag.name,
                    "to_tag": to_tag.name,
                    "amount": float(transfer.amount),
                    "amount_display": self._format_currency(float(transfer.amount)),
                    "note": transfer.note,
                },
                "remaining_budget": float(budget.get_remaining_budget()),
                "remaining_budget_display": self._format_currency(
                    float(budget.get_remaining_budget())
                ),
            }
        )


class TagTransferDeleteView(LoginRequiredView):
    """Delete a tag transfer for the budget month."""

    def _format_currency(self, val: float) -> str:
        return intcomma(f"{val:,.2f}")

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(
            Budget, month=budget_date, is_archived=False, user=request.user
        )

        transfer_id = request.POST.get("transfer_id")
        if not transfer_id:
            return JsonResponse(
                {"status": "error", "message": "Transfer ID is required"},
                status=400,
            )

        transfer = get_object_or_404(TagTransfer, id=transfer_id, budget=budget)
        transfer.delete()

        return JsonResponse(
            {
                "status": "success",
                "message": "Transfer deleted.",
                "remaining_budget": float(budget.get_remaining_budget()),
                "remaining_budget_display": self._format_currency(
                    float(budget.get_remaining_budget())
                ),
            }
        )
