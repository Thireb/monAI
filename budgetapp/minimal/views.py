import calendar
from datetime import date

from django.contrib.humanize.templatetags.humanize import intcomma
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from budgetapp.forms import ExpenseForm
from budgetapp.models import Budget, Category, IncomeHistory


class HomeView(TemplateView):
    template_name = "minimal/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        months = [calendar.month_name[i] for i in range(1, 13)]
        abbrs = [calendar.month_abbr[i] for i in range(1, 13)]
        today = date.today()
        budgets_by_month = {b.month.month: b for b in Budget.objects.filter(is_archived=False)}
        months_data = []
        for i, (month_name, abbr) in enumerate(zip(months, abbrs), 1):
            if i < today.month:
                status = "past" if i in budgets_by_month else "future"
            elif i == today.month:
                status = "current" if i in budgets_by_month else "future"
            else:
                status = "future-created" if i in budgets_by_month else "future"
            months_data.append({"name": month_name, "abbr": abbr, "status": status})
        # Group into 3 rows of 4 months each, right-to-left
        months_grid = []
        for i in range(0, 12, 4):
            row = months_data[i : i + 4][::-1]  # reverse for right-to-left
            months_grid.append(row)
        context["months_grid"] = months_grid
        context["year"] = today.year
        return context


class BudgetDetailView(TemplateView):
    template_name = "minimal/budget_detail_pages/budget_detail.html"

    def _format_currency(self, val: float) -> str:
        """
        Format a float value as a string with comma as thousands separator and two decimal places.
        Example: 12345.67 -> '12,345.67'
        """
        return intcomma(f"{val:,.2f}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year")
        month = self.kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(Budget, month=budget_date)

        # Get all expenses for this budget
        expenses_qs = budget.expenses.all().order_by("created_at")
        total_expenses = sum(e.amount for e in expenses_qs)
        categories = Category.objects.all()
        income_history = IncomeHistory.objects.filter(budget=budget)[:5]

        # Format numbers for display
        budget_income_display = self._format_currency(budget.income)
        total_expenses_display = self._format_currency(total_expenses)
        remaining_budget_display = self._format_currency(budget.get_remaining_budget())

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
            expenses.append(
                {
                    "id": expense.id,
                    "name": expense.name,
                    "amount": expense.amount,
                    "amount_display": self._format_currency(expense.amount),
                    "category": expense.category,
                    "get_tag_display": expense.get_tag_display(),
                    "is_recurring": expense.is_recurring,
                    "sub_expenses": sub_expenses,
                    "sub_expenses_exists": expense.sub_expenses.exists(),
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
                percent = (data["amount"] / float(total_expenses) * 100) if total_expenses else 0
                expenses_by_category[cat] = {
                    "amount": data["amount"],
                    "amount_display": self._format_currency(data["amount"]),
                    "color": data["color"],
                    "percentage": percent,
                    "percentage_display": f"{percent:.1f}",
                }

        context.update(
            {
                "budget": budget,
                "expenses": expenses,
                "categories": categories,
                "total_expenses": total_expenses,
                "income_history": income_history,
                "currency_choices": Budget.get_currency_choices(),
                "form": ExpenseForm(),
                "budget_income_display": budget_income_display,
                "total_expenses_display": total_expenses_display,
                "remaining_budget_display": remaining_budget_display,
                "expenses_by_category": expenses_by_category,
            }
        )
        return context
