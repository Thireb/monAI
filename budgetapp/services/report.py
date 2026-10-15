"""The monthly PDF report: its figures, the PDF file and the email that sends it.

The figures come from ``Budget.get_summary_display_strings`` and
``Budget.get_tag_account_breakdown``, so the PDF uses the same money rules as the app.
A percent is the share of the gross amount (the sum of the line amounts).
The email goes out with the user's own Resend key (``accounts.email_utils``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from io import BytesIO
from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.loader import render_to_string
from django.utils import timezone

from accounts.email_utils import get_user_resend_credentials, resend_not_configured_message
from budgetapp.models import Budget

logger = logging.getLogger(__name__)

ZERO = Decimal("0")
NO_CATEGORY = "Uncategorized"
NO_CATEGORY_COLOR = "#e0e0e0"
DEFAULT_TAG_COLOR = "#2196f3"


@dataclass(frozen=True)
class SendResult:
    """What happened when the report was sent: ``ok`` and a message for the user."""

    ok: bool
    message: str


def format_amount(value: Decimal) -> str:
    """Format an amount with thousands separators and 2 decimals, for example 1,250.00."""
    return str(intcomma(f"{value:,.2f}"))


def _share(amount: Decimal, gross: Decimal) -> dict[str, Any]:
    """The amount and its percent of ``gross``, with display strings."""
    percent = amount / gross * 100 if gross else ZERO
    return {
        "amount": amount,
        "amount_display": format_amount(amount),
        "percentage": percent,
        "percentage_display": f"{percent:.1f}",
    }


def report_context(budget: Budget) -> dict[str, Any]:
    """Build the template context of the PDF report of ``budget``."""
    lines = list(
        budget.expenses.select_related("category", "tag_foreign_key")
        .prefetch_related("sub_expenses")
        .order_by("created_at")
    )
    displays = budget.get_summary_display_strings(format_amount)
    gross = sum((line.amount for line in lines), ZERO)

    expenses = []
    for line in lines:
        subexpense_total = line.subexpense_total
        expenses.append(
            {
                "id": line.id,
                "name": line.name,
                "amount": line.amount,
                "amount_display": format_amount(line.amount),
                "category": line.category,
                "tag_foreign_key": line.tag_foreign_key,
                "is_recurring": line.is_recurring,
                "sub_expenses": [
                    {
                        "id": sub.id,
                        "name": sub.name,
                        "amount": sub.amount,
                        "amount_display": format_amount(sub.amount),
                        "is_return": sub.is_return,
                    }
                    for sub in line.sub_expenses.all()
                ],
                "subexpense_total": subexpense_total,
                "subexpense_total_display": format_amount(subexpense_total),
            }
        )

    category_totals: dict[str, Decimal] = {}
    category_colors: dict[str, str] = {}
    for line in lines:
        name = line.category.name if line.category else NO_CATEGORY
        category_totals[name] = category_totals.get(name, ZERO) + line.amount
        category_colors[name] = line.category.color if line.category else NO_CATEGORY_COLOR
    expenses_by_category = {
        name: {**_share(amount, gross), "color": category_colors[name]}
        for name, amount in category_totals.items()
    }

    tag_breakdown = {}
    for tag_name, data in budget.get_tag_account_breakdown().items():
        amount = Decimal(data["amount"])
        if amount == 0:
            continue
        tag_breakdown[tag_name] = {
            **_share(amount, gross),
            "color": data.get("color", DEFAULT_TAG_COLOR),
        }

    return {
        "budget": budget,
        "expenses": expenses,
        **displays,
        "expenses_by_category": expenses_by_category,
        "tag_breakdown": tag_breakdown,
        "generated_date": timezone.now(),
    }


def render_pdf(context: dict[str, Any]) -> bytes:
    """Render the report template to PDF bytes with WeasyPrint."""
    from weasyprint import HTML

    buffer = BytesIO()
    HTML(string=render_to_string("app/pdf/budget_report.html", context)).write_pdf(buffer)
    return buffer.getvalue()


def _send_with_resend(
    to_email: str, pdf_bytes: bytes, budget: Budget, api_key: str, from_email: str
) -> None:
    """Send the PDF as an attachment with the user's Resend key."""
    import resend

    resend.api_key = api_key
    month_name = budget.month.strftime("%B %Y")
    params: resend.Emails.SendParams = {
        "from": from_email,
        "to": [to_email],
        "subject": f"Budget Report - {month_name}",
        "html": f"""
            <h2>Your Budget Report is Ready!</h2>
            <p>Hi there,</p>
            <p>Please find attached your budget report for <strong>{month_name}</strong>.</p>
            <p>
                This report includes your income, expenses, category breakdown,
                and detailed expense list.
            </p>
            <p>Best regards,<br>monAI Budget Tracker</p>
        """,
        "attachments": [
            {
                "filename": f"budget_report_{budget.month:%Y_%m}.pdf",
                "content": list(pdf_bytes),
                "content_type": "application/pdf",
            }
        ],
    }
    resend.Emails.send(params)


def send_report(user: AbstractBaseUser, budget: Budget) -> SendResult:
    """Make the PDF report of ``budget`` and email it to ``user``."""
    to_email = getattr(user, "email", "")
    if not to_email:
        return SendResult(
            False,
            "No email address found for your account. "
            "Please update your profile with an email address.",
        )
    credentials = get_user_resend_credentials(user)
    if not credentials:
        return SendResult(False, resend_not_configured_message())
    api_key, from_email = credentials
    try:
        _send_with_resend(to_email, render_pdf(report_context(budget)), budget, api_key, from_email)
    except Exception:
        logger.exception("Could not make or send the PDF report of budget %s", budget.pk)
        return SendResult(
            False, "Failed to generate or send the budget report. Please try again later."
        )
    logger.info("Sent the PDF report of %s to user %s", budget.month, user.pk)
    return SendResult(True, f"Budget report has been sent to {to_email}")
