"""Quick add: turn ``groceries 2500 #cash`` into a spend on the right expense line.

Grammar (word order is free):

- ``2500``, ``2,500``, ``2500.50`` or ``2.5k`` is the amount (exactly 1 is needed).
- ``#cash`` limits the match to lines of the account tag whose name starts with ``cash``.
- All other words name the line. They match the line name, then the category name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from budgetapp.models import Budget, Expense, SubExpense

AMOUNT_RE = re.compile(r"^(\d[\d,]*(?:\.\d{1,2})?)(k)?$", re.IGNORECASE)
MAX_AMOUNT = Decimal("99999999.99")


class QuickAddError(ValueError):
    """The text or the amount cannot be used. The message is shown to the user."""


@dataclass(frozen=True)
class ParsedSpend:
    """The parts of a quick-add text."""

    amount: Decimal
    words: str
    account: str


def parse_amount(raw: str) -> Decimal:
    """Parse ``2500``, ``2,500``, ``2500.50`` or ``2.5k``; raise ``QuickAddError`` if invalid."""
    match = AMOUNT_RE.match(raw.strip())
    if not match:
        raise QuickAddError("Enter an amount, for example 2500.")
    try:
        amount = Decimal(match.group(1).replace(",", ""))
    except InvalidOperation as exc:
        raise QuickAddError("Enter an amount, for example 2500.") from exc
    if match.group(2):
        amount *= 1000
    amount = amount.quantize(Decimal("0.01"))
    if amount <= 0:
        raise QuickAddError("The amount must be more than 0.")
    if amount > MAX_AMOUNT:
        raise QuickAddError("The amount is too large.")
    return amount


def parse_spend_text(text: str) -> ParsedSpend:
    """Split quick-add text into amount, line words and account."""
    amounts: list[Decimal] = []
    words: list[str] = []
    account = ""
    for token in text.split():
        if token.startswith("#") and len(token) > 1:
            account = token[1:].lower()
        elif AMOUNT_RE.match(token):
            amounts.append(parse_amount(token))
        else:
            words.append(token)
    if not amounts:
        raise QuickAddError("Add an amount, for example: groceries 2500 #cash")
    if len(amounts) > 1:
        raise QuickAddError("Use only 1 amount.")
    return ParsedSpend(amount=amounts[0], words=" ".join(words).strip(), account=account)


def match_lines(budget: Budget, words: str, account: str = "") -> list[Expense]:
    """Return the lines of ``budget`` that ``words`` (and ``account``) point to.

    The first rule that finds a line wins: exact name, name starts with the words,
    name contains the words, category name starts with the words.
    """
    lines = list(budget.expenses.select_related("category", "tag_foreign_key").order_by("name"))
    if account:
        lines = [
            e
            for e in lines
            if e.tag_foreign_key and e.tag_foreign_key.name.lower().startswith(account)
        ]
    query = words.lower().strip()
    if not query:
        return lines if len(lines) == 1 else []
    rules = (
        lambda e: e.name.lower() == query,
        lambda e: e.name.lower().startswith(query),
        lambda e: query in e.name.lower(),
        lambda e: bool(e.category) and e.category.name.lower().startswith(query),
    )
    for rule in rules:
        found = [e for e in lines if rule(e)]
        if found:
            return found
    return []


def record_spend(line: Expense, amount: Decimal, note: str = "") -> SubExpense:
    """Record a spend on ``line``. The note, or the line name, names the sub-expense."""
    name = (note or line.name).strip()[:200]
    return SubExpense.objects.create(expense=line, name=name, amount=amount, is_return=False)
