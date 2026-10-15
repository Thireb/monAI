"""Goals page of the new UI: savings goals and debts, with their quick actions.

The small forms (add to a goal, repay, borrow) answer with a toast. After a change, the
response triggers ``goalsChanged`` (the panel refreshes itself) and, for a milestone or a
paid-off debt, ``celebrate`` (confetti).
"""

from __future__ import annotations

import json
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from budgetapp.app.forms import DebtEditForm, DebtForm, GoalEditForm, GoalForm
from budgetapp.models import Budget, Debt, DebtTransaction, Expense, Goal, GoalContribution
from budgetapp.services.goals import (
    add_repayment,
    debt_view,
    debt_views,
    goal_view,
    goal_views,
    milestone_passed,
    sync_goal_amount,
)
from budgetapp.services.month import build_month_snapshot
from budgetapp.services.quick_add import QuickAddError, parse_amount
from budgetapp.templatetags.app_format import money

from .base import AppTemplateView, month_url, quick_add_context, sheet_done


def panel_context(request: HttpRequest) -> dict[str, Any]:
    """Goals and debts of the user, for the page and its panel."""
    today = timezone.localdate()
    return {
        "goals": goal_views(request.user),
        "debts": debt_views(request.user, today),
        "today": today,
        "month_url": month_url(today),
    }


def toast(
    request: HttpRequest,
    message: str,
    *,
    title: str = "",
    error: bool = False,
    celebrate: bool = False,
) -> HttpResponse:
    """Answer a small form with a toast. A success also refreshes the goals panel."""
    response = render(
        request,
        "app/partials/toast.html",
        {"message": message, "title": title, "error": error},
    )
    if not error:
        events: dict[str, bool] = {"goalsChanged": True}
        if celebrate:
            events["celebrate"] = True
        response["HX-Trigger"] = json.dumps(events)
    return response


class GoalsView(AppTemplateView):
    """Savings goals with progress rings, and debts with payoff dates."""

    template_name = "app/goals.html"
    nav = "goals"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Goals, debts and the two "new" forms."""
        context = super().get_context_data(**kwargs)
        context.update(panel_context(self.request))
        context["goal_form"] = GoalForm(prefix="goal")
        context["debt_form"] = DebtForm(prefix="debt")
        today = context["today"]
        budget = Budget.objects.filter(user=self.request.user, month=today.replace(day=1)).first()
        if budget is not None:
            context["quick_add"] = quick_add_context(budget, build_month_snapshot(budget, today))
        return context


class GoalsPanelView(LoginRequiredMixin, View):
    """HTMX partial: the goals and debts lists, after a change."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render the panel."""
        return render(request, "app/partials/goals_panel.html", panel_context(request))


class GoalCreateView(LoginRequiredMixin, View):
    """Start a savings goal (form on the goals page)."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Save the goal and its starting amount, or return the form with its errors."""
        form = GoalForm(request.POST, prefix="goal")
        if not form.is_valid():
            return render(request, "app/partials/goal_form.html", {"goal_form": form})
        goal = form.save(commit=False)
        goal.user = request.user
        goal.save()
        saved = form.cleaned_data.get("saved")
        if saved:
            GoalContribution.objects.create(goal=goal, amount=saved, source="Starting amount")
            sync_goal_amount(goal)
        response = render(
            request,
            "app/partials/goal_form.html",
            {"goal_form": GoalForm(prefix="goal"), "saved_name": goal.name},
        )
        response["HX-Trigger"] = "goalsChanged"
        return response


class GoalContributeView(LoginRequiredMixin, View):
    """Add money to a goal. Passing 25, 50, 75 or 100 % gets a celebration."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Save the contribution and answer with a toast."""
        goal = get_object_or_404(Goal, pk=pk, user=request.user, is_active=True)
        try:
            amount = parse_amount(request.POST.get("amount", ""))
        except QuickAddError as exc:
            return toast(request, str(exc), error=True)
        sync_goal_amount(goal)
        before = goal_view(goal).pct
        GoalContribution.objects.create(goal=goal, amount=amount, source="monAI app")
        sync_goal_amount(goal)
        after = goal_view(goal)
        milestone = milestone_passed(before, after.pct)
        if milestone == 100:
            return toast(
                request, f"You reached {goal.name}!", title="Goal reached!", celebrate=True
            )
        if milestone:
            return toast(
                request,
                f"{goal.name} is {milestone}% done. {money(after.left)} to go.",
                title=f"{milestone}%!",
                celebrate=True,
            )
        return toast(request, f"Added {money(amount)} to {goal.name}.")


class DebtCreateView(LoginRequiredMixin, View):
    """Add a debt (form on the goals page)."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Save the debt and what is already borrowed, or return the form with its errors."""
        form = DebtForm(request.POST, prefix="debt")
        if not form.is_valid():
            return render(request, "app/partials/debt_form.html", {"debt_form": form})
        debt = form.save(commit=False)
        debt.user = request.user
        debt.save()
        borrowed = form.cleaned_data.get("borrowed")
        if borrowed:
            DebtTransaction.objects.create(debt=debt, amount=borrowed, notes="Starting amount")
            debt.recalculate_borrowed_amount()
        response = render(
            request,
            "app/partials/debt_form.html",
            {"debt_form": DebtForm(prefix="debt"), "saved_name": debt.name},
        )
        response["HX-Trigger"] = "goalsChanged"
        return response


class DebtRepayView(LoginRequiredMixin, View):
    """Add a repayment to the debt's line in this month's budget."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Save the repayment and answer with a toast; a paid-off debt gets a celebration."""
        debt = get_object_or_404(
            Debt.objects.select_related("debt_tag"), pk=pk, user=request.user, is_active=True
        )
        try:
            amount = parse_amount(request.POST.get("amount", ""))
        except QuickAddError as exc:
            return toast(request, str(exc), error=True)
        today = timezone.localdate()
        budget = Budget.objects.filter(user=request.user, month=today.replace(day=1)).first()
        if budget is None or budget.is_archived:
            return toast(request, "Start this month's budget first.", error=True)
        line = add_repayment(debt, budget, amount)
        view = debt_view(debt, today)
        if view.is_paid_off:
            return toast(request, f"{debt.name} is paid off!", title="Debt free!", celebrate=True)
        return toast(request, f"Added {money(amount)} to the line {line.name} in this month.")


class DebtBorrowView(LoginRequiredMixin, View):
    """Record more money borrowed on a debt, up to its limit."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Save the borrowing and answer with a toast."""
        debt = get_object_or_404(Debt, pk=pk, user=request.user, is_active=True)
        try:
            amount = parse_amount(request.POST.get("amount", ""))
        except QuickAddError as exc:
            return toast(request, str(exc), error=True)
        if debt.borrowed_amount + amount > debt.total_amount:
            room = debt.total_amount - debt.borrowed_amount
            return toast(request, f"You can borrow {money(room)} more at most.", error=True)
        DebtTransaction.objects.create(debt=debt, amount=amount)
        debt.recalculate_borrowed_amount()
        return toast(request, f"Recorded {money(amount)} borrowed for {debt.name}.")


def render_goal_sheet(
    request: HttpRequest, goal: Goal, form: GoalEditForm | None = None, message: str = ""
) -> HttpResponse:
    """The goal's edit sheet: its form, its contributions and the delete button."""
    context = {
        "goal": goal,
        "form": form or GoalEditForm(instance=goal, prefix="goal"),
        "contributions": goal.contributions.order_by("-date", "-id"),
        "message": message,
    }
    return render(request, "app/partials/goal_sheet.html", context)


def render_debt_sheet(
    request: HttpRequest, debt: Debt, form: DebtEditForm | None = None, message: str = ""
) -> HttpResponse:
    """The debt's edit sheet: its form, its borrowings, its repayment lines and delete."""
    repayments = (
        Expense.objects.filter(tag_foreign_key=debt.debt_tag, budget__user=request.user)
        .select_related("budget")
        .order_by("-budget__month")
        if debt.debt_tag
        else Expense.objects.none()
    )
    context = {
        "debt": debt,
        "form": form or DebtEditForm(instance=debt, prefix="debt"),
        "borrowings": debt.transactions.order_by("-date", "-id"),
        "repayments": repayments,
        "message": message,
    }
    return render(request, "app/partials/debt_sheet.html", context)


def changed(response: HttpResponse) -> HttpResponse:
    """Mark a sheet answer as a change, so the goals panel refreshes."""
    response["HX-Trigger"] = "goalsChanged"
    return response


class GoalSheetView(LoginRequiredMixin, View):
    """A goal's edit sheet: GET shows it, POST saves the goal."""

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Show the sheet."""
        return render_goal_sheet(request, get_object_or_404(Goal, pk=pk, user=request.user))

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Save the goal, or show the form errors."""
        goal = get_object_or_404(Goal, pk=pk, user=request.user)
        form = GoalEditForm(request.POST, instance=goal, prefix="goal")
        if not form.is_valid():
            return render_goal_sheet(request, goal, form=form)
        goal = form.save()
        return changed(render_goal_sheet(request, goal, message="Saved."))


class GoalDeleteView(LoginRequiredMixin, View):
    """Delete a goal and its contributions."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Delete the goal and close the sheet."""
        goal = get_object_or_404(Goal, pk=pk, user=request.user)
        name = goal.name
        goal.delete()
        return sheet_done(request, f'Deleted the goal "{name}".', "goalsChanged")


class ContributionDeleteView(LoginRequiredMixin, View):
    """Delete one contribution of a goal."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Delete it, update the goal's amount and show the sheet again."""
        contribution = get_object_or_404(
            GoalContribution.objects.select_related("goal"), pk=pk, goal__user=request.user
        )
        goal = contribution.goal
        contribution.delete()
        sync_goal_amount(goal)
        return changed(render_goal_sheet(request, goal, message="Deleted the contribution."))


class DebtSheetView(LoginRequiredMixin, View):
    """A debt's edit sheet: GET shows it, POST saves the debt."""

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Show the sheet."""
        return render_debt_sheet(request, get_object_or_404(Debt, pk=pk, user=request.user))

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Save the debt, or show the form errors."""
        debt = get_object_or_404(Debt, pk=pk, user=request.user)
        form = DebtEditForm(request.POST, instance=debt, prefix="debt")
        if not form.is_valid():
            return render_debt_sheet(request, debt, form=form)
        debt = form.save()
        return changed(render_debt_sheet(request, debt, message="Saved."))


class DebtDeleteView(LoginRequiredMixin, View):
    """Delete a debt, and its account when no other debt uses it (as on the classic page)."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Delete the debt and close the sheet. Repayment lines stay, without the account."""
        debt = get_object_or_404(Debt, pk=pk, user=request.user)
        name, tag = debt.name, debt.debt_tag
        debt.delete()
        if tag and not tag.debts.exists():
            tag.delete()
        return sheet_done(request, f'Deleted the debt "{name}".', "goalsChanged", "monthChanged")


class BorrowingDeleteView(LoginRequiredMixin, View):
    """Delete one borrowing of a debt."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Delete it, update the borrowed amount and show the sheet again."""
        borrowing = get_object_or_404(
            DebtTransaction.objects.select_related("debt"), pk=pk, debt__user=request.user
        )
        debt = borrowing.debt
        borrowing.delete()
        debt.recalculate_borrowed_amount()
        return changed(render_debt_sheet(request, debt, message="Deleted the borrowing."))
