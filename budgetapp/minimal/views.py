import calendar
from datetime import date

from django.views.generic import TemplateView

from budgetapp.models import Budget


class HomeView(TemplateView):
    template_name = "minimal/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        months = [calendar.month_name[i] for i in range(1, 13)]
        today = date.today()
        budgets_by_month = {b.month.month: b for b in Budget.objects.filter(is_archived=False)}
        months_data = []
        for i, month_name in enumerate(months, 1):
            if i < today.month:
                status = "past" if i in budgets_by_month else "future"
            elif i == today.month:
                status = "current" if i in budgets_by_month else "future"
            else:
                status = "future-created" if i in budgets_by_month else "future"
            months_data.append({"name": month_name, "status": status})
        # Group into 3 rows of 4 months each, right-to-left
        months_grid = []
        for i in range(0, 12, 4):
            row = months_data[i : i + 4][::-1]  # reverse for right-to-left
            months_grid.append(row)
        context["months_grid"] = months_grid
        context["year"] = today.year
        return context
