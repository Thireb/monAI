"""Budget CRUD views."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.humanize.templatetags.humanize import intcomma
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from budgetapp.bill_reminder_utils import apply_bill_reminders_to_budget
from budgetapp.models import BillReminder, Budget, Category, Expense, IncomeHistory, Tag

from .base import LoginRequiredTemplateView, LoginRequiredView

logger = logging.getLogger(__name__)


class BudgetDetailView(LoginRequiredTemplateView):
    """Display budget detail page with expenses, stats, and bill reminders."""

    template_name = "minimal/budget_detail_pages/budget_detail.html"

    def _format_currency(self, val: float) -> str:
        """Format a float value with comma separator and two decimal places."""
        return intcomma(f"{val:,.2f}")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Build budget detail context with expenses and category/tag breakdowns."""
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year")
        month = self.kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(
            Budget, month=budget_date, is_archived=False, user=self.request.user
        )

        expenses_qs = (
            budget.expenses.all()
            .select_related("category", "tag_foreign_key", "bill_reminder")
            .order_by("created_at")
        )
        categories = Category.objects.filter(user=self.request.user)
        tags = Tag.objects.filter(user=self.request.user).order_by("name")

        displays = budget.get_summary_display_strings(self._format_currency)

        expenses = []
        for expense in expenses_qs:
            sub_expenses = [
                {
                    "id": sub.id,
                    "name": sub.name,
                    "amount": sub.amount,
                    "amount_display": self._format_currency(sub.amount),
                    "is_return": sub.is_return,
                }
                for sub in expense.sub_expenses.all()
            ]
            subexpense_total = expense.subexpense_total
            expense_returns = expense.get_total_returns()
            remaining_amount = expense.get_remaining_amount()
            expenses.append(
                {
                    "id": expense.id,
                    "name": expense.name,
                    "amount": expense.amount,
                    "amount_display": self._format_currency(expense.amount),
                    "category": expense.category,
                    "tag_foreign_key": expense.tag_foreign_key,
                    "get_tag_display": (
                        expense.tag_foreign_key.name if expense.tag_foreign_key else "None"
                    ),
                    "is_recurring": expense.is_recurring,
                    "sub_expenses": sub_expenses,
                    "sub_expenses_exists": expense.sub_expenses.exists(),
                    "subexpense_total": subexpense_total,
                    "subexpense_total_display": self._format_currency(subexpense_total),
                    "returns": expense_returns,
                    "total_returns": self._format_currency(float(expense_returns)),
                    "remaining_amount": self._format_currency(float(remaining_amount)),
                    "bill_reminder_id": expense.bill_reminder_id,
                    "bill_reminder_next": (
                        expense.bill_reminder.next_bill_date.isoformat()
                        if expense.bill_reminder_id
                        else ""
                    ),
                    "bill_reminder_days": (
                        expense.bill_reminder.remind_days_before if expense.bill_reminder_id else 30
                    ),
                    "bill_reminder_severity": (
                        expense.bill_reminder.severity if expense.bill_reminder_id else "medium"
                    ),
                    "bill_reminder_recurrence": (
                        expense.bill_reminder.recurrence_months
                        if expense.bill_reminder_id
                        else 12
                    ),
                }
            )

        expenses_by_category = {}
        if expenses_qs.exists():
            category_totals = {}
            for expense in expenses_qs:
                cat = expense.category.name if expense.category else "Uncategorized"
                if cat not in category_totals:
                    category_totals[cat] = {
                        "amount": 0,
                        "color": expense.category.color if expense.category else "#e0e0e0",
                    }
                category_totals[cat]["amount"] += float(expense.amount)
            for cat, data in category_totals.items():
                denom = float(displays["gross_budgeted_expenses"])
                percent = (data["amount"] / denom * 100) if denom else 0
                expenses_by_category[cat] = {
                    "amount": data["amount"],
                    "amount_display": self._format_currency(data["amount"]),
                    "color": data["color"],
                    "percentage": percent,
                    "percentage_display": f"{percent:.1f}",
                }

        tag_totals = {}
        tag_labels = {}
        for expense in expenses_qs:
            if expense.tag_foreign_key:
                tag_name = expense.tag_foreign_key.name
                if tag_name not in tag_totals:
                    tag_totals[tag_name] = 0
                    tag_labels[tag_name] = tag_name
                tag_totals[tag_name] += float(expense.amount)

        context.update(
            {
                "budget": budget,
                "expenses": expenses,
                "categories": categories,
                "tags": tags,
                "currency_choices": Budget.get_currency_choices(),
                "expenses_by_category": expenses_by_category,
                "tag_totals": tag_totals,
                "tag_labels": tag_labels,
                "bill_reminder_defaults_url": reverse("minimal:bill_reminder_defaults"),
                "bill_reminder_severity_choices": BillReminder.Severity.choices,
                **displays,
            }
        )
        return context


class BudgetCreateView(LoginRequiredView):
    """Class-based view for creating a new budget."""

    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Show modal to choose between blank budget or copy from previous."""
        return JsonResponse(
            {
                "status": "success",
                "showModal": True,
                "title": "Create New Budget",
                "message": "Would you like to create a blank "
                "budget or copy recurring expenses from the previous budget?",
            }
        )

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Create a budget, optionally copying recurring expenses."""
        copy_recurring_param = request.POST.get("copy_recurring", "true")
        copy_recurring = copy_recurring_param.lower() == "true"

        target_year = request.POST.get("target_year")
        target_month = request.POST.get("target_month")

        if target_year and target_month:
            target_month_date = timezone.datetime(
                year=int(target_year), month=int(target_month), day=1
            ).date()
        else:
            last_budget = Budget.objects.filter(user=request.user).order_by("-month").first()
            if last_budget:
                target_month_date = (
                    last_budget.month.replace(day=1) + timedelta(days=32)
                ).replace(day=1)
            else:
                target_month_date = timezone.now().date().replace(day=1)

        if Budget.objects.filter(
            user=request.user, month=target_month_date, is_archived=False
        ).exists():
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Budget for {target_month_date.strftime('%B %Y')} already exists.",
                },
                status=400,
            )

        budget = Budget.objects.create(user=request.user, month=target_month_date)

        if copy_recurring:
            previous_budget = (
                Budget.objects.filter(user=request.user, month__lt=target_month_date)
                .order_by("-month")
                .first()
            )
            if previous_budget:
                budget.income = previous_budget.income
                budget.save()

                recurring_expenses = previous_budget.expenses.filter(is_recurring=True)
                for expense in recurring_expenses:
                    Expense.objects.create(
                        budget=budget,
                        name=expense.name,
                        amount=expense.amount,
                        is_recurring=True,
                        category=expense.category,
                        tag_foreign_key=expense.tag_foreign_key,
                    )
                if recurring_expenses.exists():
                    messages.success(
                        request,
                        f"Copied income and "
                        f"{recurring_expenses.count()} recurring expense(s) from previous budget",
                    )
                else:
                    messages.success(request, "Copied income from previous budget")
            else:
                messages.error(request, "No previous budget found to copy from")

        messages.success(
            request, f'Budget for {target_month_date.strftime("%B %Y")} has been created'
        )

        added = apply_bill_reminders_to_budget(budget)
        if added:
            messages.info(
                request,
                f"Added {added} scheduled bill line item(s) from your bill reminders.",
            )

        redirect_url = reverse(
            "minimal:budget_detail",
            kwargs={"year": target_month_date.year, "month": target_month_date.month},
        )
        return JsonResponse(
            {
                "status": "success",
                "message": f'Budget for {target_month_date.strftime("%B %Y")} has been created',
                "redirect": redirect_url,
            }
        )


class BudgetDeleteView(LoginRequiredView):
    """Class-based view for deleting a budget."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Delete the budget for the given year/month."""
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()

        try:
            budget = Budget.objects.get(user=request.user, month=budget_date)
        except Budget.DoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Budget for {budget_date.strftime('%B %Y')} does not exist.",
                },
                status=404,
            )

        budget_month_str = budget.month.strftime("%B %Y")
        budget.delete()

        messages.success(request, f"Budget for {budget_month_str} has been deleted")

        return JsonResponse(
            {
                "status": "success",
                "message": f"Budget for {budget_month_str} has been successfully deleted.",
            }
        )


class IncomeUpdateView(LoginRequiredView):
    """Class-based view for updating budget income."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Update budget income, currency, and log the change."""
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(
            Budget, month=budget_date, is_archived=False, user=self.request.user
        )

        income = request.POST.get("income")
        currency = request.POST.get("currency")
        reason = request.POST.get("reason")

        if income:
            old_income = budget.income
            old_currency = budget.currency

            budget.income = Decimal(income)
            budget.currency = currency
            budget.save()

            IncomeHistory.objects.create(
                budget=budget,
                old_amount=old_income,
                new_amount=budget.income,
                old_currency=old_currency,
                new_currency=currency,
                reason=reason,
            )

            income_display = intcomma(f"{float(budget.income):,.2f}")
            displays = budget.get_summary_display_strings(lambda v: intcomma(f"{float(v):,.2f}"))
            remaining_budget = budget.get_remaining_budget()

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Income updated successfully!",
                    "income": float(budget.income),
                    "income_display": income_display,
                    "currency": currency,
                    "remaining_budget": float(remaining_budget),
                    "remaining_budget_display": displays["remaining_budget_display"],
                    "gross_expenses_display": displays["gross_expenses_display"],
                    "total_returns_display": displays["total_returns_display"],
                    "net_expenses_display": displays["net_expenses_display"],
                }
            )

        return JsonResponse({"status": "error", "message": "Income value is required"}, status=400)


class SummaryCardsView(LoginRequiredView):
    """View for getting summary cards."""

    def _format_currency(self, val: float) -> str:
        """Format a float value with comma separator and two decimal places."""
        return intcomma(f"{val:,.2f}")

    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Return rendered summary cards HTML for the budget month."""
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(
            Budget, month=budget_date, is_archived=False, user=self.request.user
        )

        displays = budget.get_summary_display_strings(self._format_currency)

        html = render_to_string(
            "minimal/budget_detail_pages/summary_cards.html",
            {
                "budget": budget,
                **displays,
            },
        )

        return JsonResponse({"html": html})


class BudgetEmailPDFView(LoginRequiredView):
    """Generate a budget PDF and email it to the user via Resend."""

    def _format_currency(self, val: float) -> str:
        """Format a float value with comma separator and two decimal places."""
        return intcomma(f"{val:,.2f}")

    def _get_budget_context(self, budget: Budget) -> dict[str, Any]:
        """Build context data for PDF rendering."""
        expenses_qs = budget.expenses.all().order_by("created_at")
        displays = budget.get_summary_display_strings(self._format_currency)
        gross_budgeted = displays["gross_budgeted_expenses"]

        expenses = []
        for expense in expenses_qs:
            sub_expenses = [
                {
                    "id": sub.id,
                    "name": sub.name,
                    "amount": sub.amount,
                    "amount_display": self._format_currency(sub.amount),
                    "is_return": sub.is_return,
                }
                for sub in expense.sub_expenses.all()
            ]
            subexpense_total = expense.subexpense_total
            expenses.append(
                {
                    "id": expense.id,
                    "name": expense.name,
                    "amount": expense.amount,
                    "amount_display": self._format_currency(expense.amount),
                    "category": expense.category,
                    "tag_foreign_key": expense.tag_foreign_key,
                    "is_recurring": expense.is_recurring,
                    "sub_expenses": sub_expenses,
                    "subexpense_total": subexpense_total,
                    "subexpense_total_display": self._format_currency(subexpense_total),
                }
            )

        expenses_by_category = {}
        if expenses_qs.exists():
            category_totals = {}
            for expense in expenses_qs:
                cat = expense.category.name if expense.category else "Uncategorized"
                if cat not in category_totals:
                    category_totals[cat] = {
                        "amount": 0,
                        "color": (expense.category.color if expense.category else "#e0e0e0"),
                    }
                category_totals[cat]["amount"] += float(expense.amount)
            for cat, data in category_totals.items():
                denom = float(gross_budgeted)
                percent = (data["amount"] / denom * 100) if denom else 0
                expenses_by_category[cat] = {
                    "amount": data["amount"],
                    "amount_display": self._format_currency(data["amount"]),
                    "color": data["color"],
                    "percentage": percent,
                    "percentage_display": f"{percent:.1f}",
                }

        tag_totals = {}
        tag_colors = {}
        for expense in expenses_qs:
            if expense.tag_foreign_key:
                tag_name = expense.tag_foreign_key.name
                if tag_name not in tag_totals:
                    tag_totals[tag_name] = 0
                    tag_colors[tag_name] = expense.tag_foreign_key.color
                tag_totals[tag_name] += float(expense.amount)

        tag_breakdown = {}
        for tag_name, amount in tag_totals.items():
            denom = float(gross_budgeted)
            percent = (amount / denom * 100) if denom else 0
            tag_breakdown[tag_name] = {
                "amount": amount,
                "amount_display": self._format_currency(amount),
                "color": tag_colors.get(tag_name, "#2196f3"),
                "percentage": percent,
                "percentage_display": f"{percent:.1f}",
            }

        return {
            "budget": budget,
            "expenses": expenses,
            **displays,
            "expenses_by_category": expenses_by_category,
            "tag_breakdown": tag_breakdown,
            "generated_date": timezone.now(),
        }

    def _generate_pdf(self, context: dict[str, Any]) -> bytes:
        """Generate PDF bytes from the budget report template."""
        try:
            from weasyprint import HTML
        except ImportError:
            logger.error("WeasyPrint is not installed")
            raise ImportError(
                "WeasyPrint is required for PDF generation. "
                "Install it with: pip install weasyprint"
            )

        html_string = render_to_string("minimal/pdf/budget_report.html", context)
        html = HTML(string=html_string)
        pdf_buffer = BytesIO()
        html.write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    def _send_email_with_resend(
        self,
        user_email: str,
        pdf_bytes: bytes,
        budget_month: date,
    ) -> Any:
        """Send email with PDF attachment using Resend API."""
        try:
            import resend
        except ImportError:
            logger.error("Resend SDK is not installed")
            raise ImportError(
                "Resend SDK is required for email. " "Install it with: pip install resend"
            )

        api_key = getattr(settings, "RESEND_API_KEY", "")
        from_email = getattr(settings, "RESEND_FROM_EMAIL", "onboarding@resend.dev")

        if not api_key:
            raise ValueError(
                "RESEND_API_KEY is not configured. " "Please add your Resend API key to config.yaml"
            )

        resend.api_key = api_key

        filename = f"budget_report_{budget_month.strftime('%Y_%m')}.pdf"

        params: resend.Emails.SendParams = {
            "from": from_email,
            "to": [user_email],
            "subject": f"Budget Report - {budget_month.strftime('%B %Y')}",
            "html": f"""
                <h2>Your Budget Report is Ready!</h2>
                <p>Hi there,</p>
                <p>
                    Please find attached your budget report for
                    <strong>{budget_month.strftime('%B %Y')}</strong>.
                </p>
                <p>
                    This report includes your income, expenses, category breakdown,
                    and detailed expense list.
                </p>
                <p>Best regards,<br>monAI Budget Tracker</p>
            """,
            "attachments": [
                {
                    "filename": filename,
                    "content": list(pdf_bytes),
                    "content_type": "application/pdf",
                }
            ],
        }

        response = resend.Emails.send(params)
        return response

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Generate and email a PDF budget report."""
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()

        try:
            budget = get_object_or_404(
                Budget, month=budget_date, is_archived=False, user=self.request.user
            )
        except Exception:
            return JsonResponse(
                {"status": "error", "message": "Budget not found."},
                status=404,
            )

        try:
            context = self._get_budget_context(budget)
            pdf_bytes = self._generate_pdf(context)

            user_email = request.user.email
            if not user_email:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "No email address found for your account. "
                        "Please update your profile with an email address.",
                    },
                    status=400,
                )

            self._send_email_with_resend(user_email, pdf_bytes, budget.month)

            logger.info(
                f"Budget PDF emailed successfully to {user_email} "
                f"for {budget.month.strftime('%B %Y')}"
            )

            return JsonResponse(
                {
                    "status": "success",
                    "message": f"Budget report has been sent to {user_email}",
                }
            )

        except ImportError as e:
            logger.error(f"Import error in PDF email: {e}")
            return JsonResponse(
                {
                    "status": "error",
                    "message": str(e),
                },
                status=500,
            )
        except ValueError as e:
            logger.error(f"Configuration error in PDF email: {e}")
            return JsonResponse(
                {
                    "status": "error",
                    "message": str(e),
                },
                status=500,
            )
        except Exception as e:
            logger.error(f"Error generating/sending budget PDF: {e}")
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Failed to generate or send the budget report. "
                    "Please try again later.",
                },
                status=500,
            )
