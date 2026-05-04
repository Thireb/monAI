"""
Budget CRUD views.
"""

import logging
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.humanize.templatetags.humanize import intcomma
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from budgetapp.models import Budget, Category, Expense, IncomeHistory, Tag

from .base import LoginRequiredTemplateView, LoginRequiredView

logger = logging.getLogger(__name__)


class BudgetDetailView(LoginRequiredTemplateView):
    template_name = "minimal/budget_detail_pages/budget_detail.html"

    def _format_currency(self, val: float) -> str:
        """
        Format a float value as a string with comma as thousands separator
        and two decimal places.
        """
        return intcomma(f"{val:,.2f}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year")
        month = self.kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(Budget, month=budget_date, user=self.request.user)

        # Get all expenses for this budget
        expenses_qs = budget.expenses.all().order_by("created_at")
        categories = Category.objects.filter(user=self.request.user)
        tags = Tag.objects.filter(user=self.request.user).order_by("name")

        displays = budget.get_summary_display_strings(self._format_currency)

        # Prepare expenses with amount_display and sub_expenses with amount_display
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
                }
            )

        # Prepare category stats for display
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

        # Calculate tag totals for display using tag_foreign_key
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
                **displays,
            }
        )
        return context


class BudgetCreateView(LoginRequiredView):
    """Class-based view for creating a new budget."""

    def get(self, request, *args, **kwargs):
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

    def post(self, request, *args, **kwargs):
        copy_recurring_param = request.POST.get("copy_recurring", "true")
        copy_recurring = copy_recurring_param.lower() == "true"

        target_year = request.POST.get("target_year")
        target_month = request.POST.get("target_month")

        # Determine the target month for budget creation
        if target_year and target_month:
            # Use the specified year and month
            target_month_date = timezone.datetime(
                year=int(target_year), month=int(target_month), day=1
            ).date()
        else:
            # Fallback to the original logic (next month after last budget)
            last_budget = Budget.objects.filter(user=request.user).order_by("-month").first()
            if last_budget:
                target_month_date = (
                    last_budget.month.replace(day=1) + timezone.timedelta(days=32)
                ).replace(day=1)
            else:
                target_month_date = timezone.now().date().replace(day=1)

        # Check if budget already exists for this month
        if Budget.objects.filter(user=request.user, month=target_month_date).exists():
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Budget for {target_month_date.strftime('%B %Y')} already exists.",
                },
                status=400,
            )

        # Create new budget
        budget = Budget.objects.create(user=request.user, month=target_month_date)

        # Copy recurring expenses and income from previous budget if requested
        if copy_recurring:
            # Get the budget before the one we just created
            previous_budget = (
                Budget.objects.filter(user=request.user, month__lt=target_month_date)
                .order_by("-month")
                .first()
            )
            if previous_budget:
                # Copy income from previous budget
                budget.income = previous_budget.income
                budget.save()

                # Copy recurring expenses
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
                # Add success message about copied expenses and income
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

        # Return JSON response with redirect URL
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

    def post(self, request, *args, **kwargs):
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

        # Store budget info for the message
        budget_month_str = budget.month.strftime("%B %Y")

        # Delete the budget (this will cascade delete all related data)
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

    def post(self, request, *args, **kwargs):
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(Budget, month=budget_date, user=self.request.user)

        income = request.POST.get("income")
        currency = request.POST.get("currency")
        reason = request.POST.get("reason")

        if income:
            old_income = budget.income
            old_currency = budget.currency

            budget.income = Decimal(income)
            budget.currency = currency
            budget.save()

            # Log income change
            IncomeHistory.objects.create(
                budget=budget,
                old_amount=old_income,
                new_amount=budget.income,
                old_currency=old_currency,
                new_currency=currency,
                reason=reason,
            )

            # Format for display
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
        return intcomma(f"{val:,.2f}")

    def get(self, request, *args, **kwargs):
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(Budget, month=budget_date, user=self.request.user)

        displays = budget.get_summary_display_strings(self._format_currency)

        # Render the summary cards section
        html = render_to_string(
            "minimal/budget_detail_pages/summary_cards.html",
            {
                "budget": budget,
                **displays,
            },
        )

        return JsonResponse({"html": html})


class BudgetEmailPDFView(LoginRequiredView):
    """
    View to generate a PDF of the budget and email it to the user.
    Uses WeasyPrint for PDF generation and Resend for email delivery.
    """

    def _format_currency(self, val: float) -> str:
        """Format a float value with comma separator and two decimal places."""
        return intcomma(f"{val:,.2f}")

    def _get_budget_context(self, budget):
        """
        Get the budget context data for PDF rendering.
        Reuses logic from BudgetDetailView.
        """
        expenses_qs = budget.expenses.all().order_by("created_at")
        displays = budget.get_summary_display_strings(self._format_currency)
        gross_budgeted = displays["gross_budgeted_expenses"]

        # Prepare expenses with formatted amounts and sub_expenses
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

        # Prepare category stats
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

        # Prepare tag breakdown (Account Breakdown) for PDF
        tag_totals = {}
        tag_colors = {}
        for expense in expenses_qs:
            if expense.tag_foreign_key:
                tag_name = expense.tag_foreign_key.name
                if tag_name not in tag_totals:
                    tag_totals[tag_name] = 0
                    tag_colors[tag_name] = expense.tag_foreign_key.color
                tag_totals[tag_name] += float(expense.amount)

        # Format tag breakdown similar to expenses_by_category
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

    def _generate_pdf(self, context):
        """Generate PDF from template using WeasyPrint."""
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

    def _send_email_with_resend(self, user_email, pdf_bytes, budget_month):
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

        # Resend Python SDK expects content as list of bytes
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

    def post(self, request, *args, **kwargs):
        """Handle POST request to generate and email PDF."""
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()

        try:
            budget = get_object_or_404(Budget, month=budget_date, user=self.request.user)
        except Exception:
            return JsonResponse(
                {"status": "error", "message": "Budget not found."},
                status=404,
            )

        try:
            # Get context for PDF
            context = self._get_budget_context(budget)

            # Generate PDF
            pdf_bytes = self._generate_pdf(context)

            # Send email
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
