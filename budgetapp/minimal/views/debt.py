"""Debt management views."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404

from budgetapp.models import Debt, DebtTransaction

from .base import LoginRequiredTemplateView, LoginRequiredView


class DebtListView(LoginRequiredTemplateView):
    """View for listing all debts."""

    template_name = "minimal/debts/debt_list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Return active and completed debts, updating status as needed."""
        context = super().get_context_data(**kwargs)
        active_debts = Debt.objects.filter(
            user=self.request.user, is_active=True
        ).order_by("-created_at")
        completed_debts = Debt.objects.filter(
            user=self.request.user, is_active=False
        ).order_by("-created_at")

        for debt in active_debts:
            debt.check_and_update_status()

        context.update(
            {
                "active_debts": active_debts,
                "completed_debts": completed_debts,
            }
        )
        return context


class DebtDetailView(LoginRequiredTemplateView):
    """View for displaying debt details."""

    template_name = "minimal/debts/debt_detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Return debt detail with transactions and totals."""
        context = super().get_context_data(**kwargs)
        debt_id = self.kwargs.get("debt_id")
        debt = get_object_or_404(Debt, id=debt_id, user=self.request.user)
        transactions = debt.transactions.all().order_by("-date")

        debt.check_and_update_status()

        total_borrowed = sum(t.amount for t in transactions)

        context.update(
            {
                "debt": debt,
                "transactions_page": transactions,
                "total_borrowed": total_borrowed,
            }
        )
        return context


class DebtCreateView(LoginRequiredView):
    """View for creating new debts via AJAX."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Create a debt from POST data and return JSON."""
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        total_amount = request.POST.get("total_amount")

        if not name or not total_amount:
            return JsonResponse(
                {"success": False, "error": "Name and total amount are required"}, status=400
            )

        try:
            total_amount = Decimal(total_amount)
            if total_amount <= 0:
                return JsonResponse(
                    {"success": False, "error": "Total amount must be greater than zero"},
                    status=400,
                )

            debt = Debt.objects.create(
                user=request.user, name=name, description=description, total_amount=total_amount
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Debt "{name}" created successfully!',
                    "debt": {
                        "id": debt.id,
                        "name": debt.name,
                        "description": debt.description,
                        "total_amount": str(debt.total_amount),
                        "borrowed_amount": str(debt.borrowed_amount),
                        "repaid_amount": str(debt.repaid_amount),
                        "remaining_to_repay": str(debt.remaining_to_repay),
                        "repayment_progress_percentage": debt.repayment_progress_percentage,
                        "debt_tag": debt.debt_tag.name,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error creating debt: {str(e)}"}, status=400
            )


class DebtUpdateView(LoginRequiredView):
    """View for updating debts via AJAX."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Update a debt from POST data and return JSON."""
        debt_id = request.POST.get("debt_id")
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        total_amount = request.POST.get("total_amount")

        if not debt_id or not name or not total_amount:
            return JsonResponse(
                {"success": False, "error": "Debt ID, name, and total amount are required"},
                status=400,
            )

        try:
            total_amount = Decimal(total_amount)
            if total_amount <= 0:
                return JsonResponse(
                    {"success": False, "error": "Total amount must be greater than zero"},
                    status=400,
                )

            debt = get_object_or_404(Debt, id=debt_id, user=request.user)
            debt.name = name
            debt.description = description
            debt.total_amount = total_amount
            debt.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Debt "{name}" updated successfully!',
                    "debt": {
                        "id": debt.id,
                        "name": debt.name,
                        "description": debt.description,
                        "total_amount": str(debt.total_amount),
                        "borrowed_amount": str(debt.borrowed_amount),
                        "repaid_amount": str(debt.repaid_amount),
                        "remaining_to_repay": str(debt.remaining_to_repay),
                        "progress_percentage": debt.progress_percentage,
                        "repayment_progress_percentage": debt.repayment_progress_percentage,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error updating debt: {str(e)}"}, status=400
            )


class DebtDeleteView(LoginRequiredView):
    """View for deleting debts via AJAX."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Delete a debt and its auto-generated tag when unused."""
        debt_id = request.POST.get("debt_id")

        if not debt_id:
            return JsonResponse({"success": False, "error": "Debt ID is required"}, status=400)

        try:
            debt = get_object_or_404(Debt, id=debt_id, user=request.user)
            debt_name = debt.name
            debt_tag = debt.debt_tag
            transaction_count = debt.transactions.count()

            debt.delete()

            tag_deleted = False
            if debt_tag and not debt_tag.debts.exists():
                debt_tag.delete()
                tag_deleted = True

            message = f'Debt "{debt_name}" deleted successfully!'
            if transaction_count > 0:
                message += f" ({transaction_count} transaction(s) removed)"
            if tag_deleted:
                message += " (associated tag removed)"

            return JsonResponse(
                {
                    "success": True,
                    "message": message,
                    "debt_id": debt_id,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error deleting debt: {str(e)}"}, status=400
            )


class DebtBorrowingView(LoginRequiredView):
    """View for adding borrowing transactions via AJAX."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Add a borrowing transaction to a debt."""
        debt_id = request.POST.get("debt_id")
        amount = request.POST.get("amount")
        date_str = request.POST.get("date")
        notes = request.POST.get("notes", "")

        if not debt_id or not amount or not date_str:
            return JsonResponse(
                {"success": False, "error": "Debt ID, amount, and date are required"}, status=400
            )

        try:
            amount = Decimal(amount)
            if amount <= 0:
                return JsonResponse(
                    {"success": False, "error": "Amount must be greater than zero"}, status=400
                )

            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse(
                    {"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}, status=400
                )

            debt = get_object_or_404(Debt, id=debt_id, user=request.user)

            current_borrowed = debt.borrowed_amount
            if current_borrowed + amount > debt.total_amount:
                return JsonResponse(
                    {
                        "success": False,
                        "error": (
                            f"This borrowing would exceed the total debt amount of "
                            f"{debt.total_amount}"
                        ),
                    },
                    status=400,
                )

            transaction = DebtTransaction.objects.create(
                debt=debt, amount=amount, date=parsed_date, notes=notes
            )

            debt.recalculate_borrowed_amount()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Added {amount} borrowing to "{debt.name}"',
                    "transaction": {
                        "id": transaction.id,
                        "amount": str(transaction.amount),
                        "date": transaction.date.strftime("%Y-%m-%d"),
                        "date_iso": transaction.date.strftime("%Y-%m-%d"),
                        "notes": transaction.notes,
                        "notes_escaped": (
                            transaction.notes.replace("'", "\\'") if transaction.notes else ""
                        ),
                        "created_at": transaction.created_at.strftime("%Y-%m-%d"),
                    },
                    "debt": {
                        "name": debt.name,
                        "total_amount": str(debt.total_amount),
                        "borrowed_amount": str(debt.borrowed_amount),
                        "repaid_amount": str(debt.repaid_amount),
                        "remaining_to_repay": str(debt.remaining_to_repay),
                        "progress_percentage": debt.progress_percentage,
                        "repayment_progress_percentage": debt.repayment_progress_percentage,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error adding borrowing: {str(e)}"}, status=400
            )


class DebtTransactionUpdateView(LoginRequiredView):
    """View for updating borrowing transactions via AJAX."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Update a borrowing transaction."""
        transaction_id = request.POST.get("transaction_id")
        debt_id = request.POST.get("debt_id")
        amount = request.POST.get("amount")
        date_str = request.POST.get("date")
        notes = request.POST.get("notes", "")

        if not transaction_id or not debt_id or not amount or not date_str:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Transaction ID, debt ID, amount, and date are required",
                },
                status=400,
            )

        try:
            amount = Decimal(amount)
            if amount <= 0:
                return JsonResponse(
                    {"success": False, "error": "Amount must be greater than zero"}, status=400
                )

            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse(
                    {"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}, status=400
                )

            transaction = get_object_or_404(
                DebtTransaction, id=transaction_id, debt_id=debt_id, debt__user=request.user
            )
            debt = transaction.debt

            transaction.amount = amount
            transaction.date = parsed_date
            transaction.notes = notes
            transaction.save()

            debt.recalculate_borrowed_amount()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Updated borrowing transaction for "{debt.name}"',
                    "transaction": {
                        "id": transaction.id,
                        "amount": str(transaction.amount),
                        "date": transaction.date.strftime("%Y-%m-%d"),
                        "date_iso": transaction.date.strftime("%Y-%m-%d"),
                        "notes": transaction.notes,
                        "notes_escaped": (
                            transaction.notes.replace("'", "\\'") if transaction.notes else ""
                        ),
                        "created_at": transaction.created_at.strftime("%Y-%m-%d"),
                    },
                    "debt": {
                        "name": debt.name,
                        "total_amount": str(debt.total_amount),
                        "borrowed_amount": str(debt.borrowed_amount),
                        "repaid_amount": str(debt.repaid_amount),
                        "remaining_to_repay": str(debt.remaining_to_repay),
                        "progress_percentage": debt.progress_percentage,
                        "repayment_progress_percentage": debt.repayment_progress_percentage,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error updating transaction: {str(e)}"}, status=400
            )


class DebtTransactionDeleteView(LoginRequiredView):
    """View for deleting borrowing transactions via AJAX."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Delete a borrowing transaction."""
        transaction_id = request.POST.get("transaction_id")

        if not transaction_id:
            return JsonResponse(
                {"success": False, "error": "Transaction ID is required"}, status=400
            )

        try:
            transaction = get_object_or_404(
                DebtTransaction, id=transaction_id, debt__user=request.user
            )
            debt = transaction.debt
            transaction_amount = transaction.amount

            transaction.delete()

            debt.recalculate_borrowed_amount()

            return JsonResponse(
                {
                    "success": True,
                    "message": (
                        f'Deleted borrowing transaction of {transaction_amount} '
                        f'from "{debt.name}"'
                    ),
                    "debt": {
                        "name": debt.name,
                        "total_amount": str(debt.total_amount),
                        "borrowed_amount": str(debt.borrowed_amount),
                        "repaid_amount": str(debt.repaid_amount),
                        "remaining_to_repay": str(debt.remaining_to_repay),
                        "progress_percentage": debt.progress_percentage,
                        "repayment_progress_percentage": debt.repayment_progress_percentage,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error deleting transaction: {str(e)}"}, status=400
            )
