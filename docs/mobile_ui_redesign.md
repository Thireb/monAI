# Spec: Mobile UI Redesign (Budget Core + Transfers)

## Objective

Rebuild the Flutter companion as an **action-first, mobile-native** app for managing the current month’s budget — not a clone of the minimal web dashboard. Users should glance remaining money, add expenses, filter by account tag, and transfer between accounts offline with sync.

## Scope

**In:** Budgets, expenses, sub-expenses/returns, categories, tags (accounts), tag transfers, auth/sync settings.

**Out:** Debts, goals, email PDF, bill-reminder UX, dark mode, multi-currency conversion.

## Commands

```bash
# Django
cd /path/to/monAI
source .venv/bin/activate
python manage.py migrate
python manage.py test budgetapp.tests.test_mobile_sync budgetapp.tests.test_tag_transfers

# Flutter
cd mobile/budget_mobile
flutter pub get
flutter analyze
flutter test
```

## Information architecture

- **Bottom nav — Months:** year-grouped budget list → **Month hub**.
- **Month hub:** one hero “Remaining”; secondary income/budgeted line; account chips (filter); flat expense list; primary **Add**; overflow **Transfer**.
- **Bottom nav — More:** Categories, Tags, Settings (URL, login, sync status/actions).
- Sub-expenses: via expense detail / expand-in-place, not nested ExpansionTile trees as the default.

## Visual rules

- Quicksand; monAI blue `#2196F3` / green `#4CAF50`.
- No Orbitron AppBar title; no stacked five-metric web summary; no glass card-per-row lists.
- Quiet surfaces; cards only for interactive containers when needed.
- One strong primary CTA on Month hub.

## Sync

Order: categories → tags → budgets → expenses → sub-expenses → **tag-transfers** (push then pull).

Transfer math: does not change remaining; account breakdown = expense sums ± transfers (same as web `get_tag_account_breakdown`).

## Success criteria

- [ ] Bottom nav Months / More; sync not on Months home.
- [ ] Month hub shows remaining hero + add expense + transfer.
- [ ] Filter expenses by account chip.
- [ ] Categories and tags manageable under More.
- [ ] Tag transfers sync with Django mobile API.
- [ ] `flutter analyze` clean; Django transfer sync tests pass.

## Boundaries

- **Always:** Keep offline-first dirty flags; preserve remaining-budget math parity with Django.
- **Ask first:** New domains (debts/goals), navigation beyond Months/More.
- **Never:** Replicate web summary-card stack; put sync chrome on Months list.
