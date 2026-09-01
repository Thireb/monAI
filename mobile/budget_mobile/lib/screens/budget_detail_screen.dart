import "package:flutter/material.dart";

import "../app_scope.dart";
import "../repositories/budget_repository.dart";
import "../repositories/expense_repository.dart";
import "../repositories/sub_expense_repository.dart";
import "../repositories/tag_repository.dart";
import "../repositories/tag_transfer_repository.dart";
import "../theme/minimal_theme.dart";
import "../utils/account_breakdown.dart";
import "../utils/budget_format.dart";
import "../widgets/account_chip.dart";
import "../widgets/money_text.dart";
import "budget_form_screen.dart";
import "expense_form_screen.dart";
import "sub_expense_form_screen.dart";
import "transfer_form_screen.dart";

/// Month hub: remaining hero, account filter, expenses, add / transfer.
class BudgetDetailScreen extends StatefulWidget {
  const BudgetDetailScreen({super.key, required this.budget});

  final BudgetRow budget;

  @override
  State<BudgetDetailScreen> createState() => _BudgetDetailScreenState();
}

class _BudgetDetailScreenState extends State<BudgetDetailScreen> {
  List<ExpenseRow> _expenses = [];
  List<SubExpenseRow> _subAll = [];
  List<TagRow> _tags = [];
  List<TagTransferRow> _transfers = [];
  int? _filterTagServerId;
  bool _loading = true;
  final Set<int> _expanded = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final list =
        await AppScope.expenseRepo.listForBudgetLocalId(widget.budget.localId);
    final subs =
        await AppScope.subExpenseRepo.listForBudgetLocalId(widget.budget.localId);
    final tags = await AppScope.tagRepo.listNonDeleted();
    final transfers = await AppScope.tagTransferRepo
        .listForBudgetLocalId(widget.budget.localId);
    if (!mounted) {
      return;
    }
    setState(() {
      _expenses = list;
      _subAll = subs;
      _tags = tags;
      _transfers = transfers;
      _loading = false;
    });
  }

  List<SubExpenseRow> _subsForExpense(int expenseLocalId) {
    return _subAll.where((s) => s.expenseLocalId == expenseLocalId).toList();
  }

  double _totalExpenseAllocated() {
    var t = 0.0;
    for (final e in _expenses) {
      t += e.amount;
    }
    return t;
  }

  double _totalReturnsAll() {
    var t = 0.0;
    for (final s in _subAll) {
      if (s.isReturn) {
        t += s.amount;
      }
    }
    return t;
  }

  double _remainingBudget() {
    return widget.budget.income - _totalExpenseAllocated() + _totalReturnsAll();
  }

  Color _parseHexColor(String hex) {
    var s = hex.trim();
    if (s.startsWith("#")) {
      s = s.substring(1);
    }
    if (s.length == 6) {
      final v = int.tryParse(s, radix: 16);
      if (v != null) {
        return Color(0xFF000000 | v);
      }
    }
    return MinimalColors.primaryBlue;
  }

  Future<void> _confirmDeleteExpense(ExpenseRow e) async {
    final subs = _subsForExpense(e.localId);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Delete expense?"),
        content: Text(
          subs.isEmpty
              ? "Remove \"${e.name}\"?"
              : "Remove \"${e.name}\" and ${subs.length} sub-line(s)?",
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text("Cancel"),
          ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text("Delete"),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) {
      return;
    }
    await AppScope.expenseRepo.markDeletedLocal(e.localId);
    await AppScope.budgetSync.syncExpenseDeletes();
    if (mounted) {
      await _load();
    }
  }

  Future<void> _confirmDeleteTransfer(TagTransferRow t) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Delete transfer?"),
        content: const Text("This only undoes the account move."),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text("Cancel"),
          ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text("Delete"),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) {
      return;
    }
    await AppScope.tagTransferRepo.markDeletedLocal(t.localId);
    await AppScope.budgetSync.syncTransferDeletes();
    if (mounted) {
      await _load();
    }
  }

  String _tagName(int? serverId) {
    if (serverId == null) {
      return "No account";
    }
    for (final t in _tags) {
      if (t.serverId == serverId) {
        return t.name;
      }
    }
    return "Tag #$serverId";
  }

  @override
  Widget build(BuildContext context) {
    final b = widget.budget;
    final remaining = _remainingBudget();
    final gross = _totalExpenseAllocated();
    final breakdown = buildAccountBreakdown(
      expenses: _expenses,
      transfers: _transfers,
      tags: _tags,
    );
    final filtered = _filterTagServerId == null
        ? _expenses
        : _expenses
            .where((e) => e.tagServerId == _filterTagServerId)
            .toList();

    return MinimalPageBackground(
      child: Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(formatBudgetMonthLabel(b.month)),
        actions: [
          IconButton(
            tooltip: "Edit budget",
            icon: const Icon(Icons.edit_outlined),
            onPressed: () async {
              await Navigator.of(context).push<bool>(
                MaterialPageRoute<bool>(
                  builder: (_) => BudgetFormScreen(
                    repository: AppScope.budgetRepo,
                    existing: b,
                  ),
                ),
              );
              if (mounted) {
                await _load();
              }
            },
          ),
          PopupMenuButton<String>(
            onSelected: (v) async {
              if (v == "transfer") {
                final changed = await Navigator.of(context).push<bool>(
                  MaterialPageRoute<bool>(
                    builder: (_) => TransferFormScreen(budget: b),
                  ),
                );
                if (changed == true && mounted) {
                  await _load();
                }
              }
            },
            itemBuilder: (_) => const [
              PopupMenuItem(value: "transfer", child: Text("Transfer")),
            ],
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await Navigator.of(context).push<bool>(
            MaterialPageRoute<bool>(
              builder: (_) => ExpenseFormScreen(
                budgetLocalId: b.localId,
              ),
            ),
          );
          if (mounted) {
            await _load();
          }
        },
        icon: const Icon(Icons.add),
        label: const Text("Add"),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 100),
                children: [
                  Text(
                    "Remaining",
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          color: MinimalColors.textSecondary,
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                  const SizedBox(height: 4),
                  MoneyText(
                    remaining,
                    currency: b.currency,
                    style: Theme.of(context).textTheme.displaySmall,
                  ),
                  const SizedBox(height: 6),
                  Text(
                    "Income ${formatMoneyLine(b.currency, b.income)}"
                    " · Budgeted ${formatMoneyLine(b.currency, gross)}",
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: MinimalColors.textSecondary,
                        ),
                  ),
                  if (breakdown.isNotEmpty) ...[
                    const SizedBox(height: 20),
                    Text(
                      "Accounts",
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        AccountChip(
                          label: "All",
                          selected: _filterTagServerId == null,
                          onTap: () =>
                              setState(() => _filterTagServerId = null),
                        ),
                        ...breakdown.map(
                          (row) => AccountChip(
                            label:
                                "${row.name} ${row.amount.toStringAsFixed(0)}",
                            selected: _filterTagServerId == row.tagServerId,
                            color: _parseHexColor(row.color),
                            onTap: () => setState(() {
                              _filterTagServerId =
                                  _filterTagServerId == row.tagServerId
                                      ? null
                                      : row.tagServerId;
                            }),
                          ),
                        ),
                      ],
                    ),
                  ],
                  if (_transfers.isNotEmpty) ...[
                    const SizedBox(height: 20),
                    Text(
                      "Transfers",
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                    ..._transfers.map((t) {
                      return ListTile(
                        contentPadding: EdgeInsets.zero,
                        title: Text(
                          "${_tagName(t.fromTagServerId)} → ${_tagName(t.toTagServerId)}",
                        ),
                        subtitle: t.note.isEmpty ? null : Text(t.note),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              formatMoneyLine(b.currency, t.amount),
                              style: const TextStyle(fontWeight: FontWeight.w600),
                            ),
                            IconButton(
                              icon: const Icon(Icons.delete_outline, size: 20),
                              onPressed: () => _confirmDeleteTransfer(t),
                            ),
                          ],
                        ),
                      );
                    }),
                  ],
                  const SizedBox(height: 20),
                  Text(
                    "Expenses",
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  if (filtered.isEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 16),
                      child: Text(
                        "No expenses yet. Tap Add.",
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: MinimalColors.textSecondary,
                            ),
                      ),
                    ),
                  ...filtered.map((e) {
                    final open = _expanded.contains(e.localId);
                    final subs = _subsForExpense(e.localId);
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text(
                            e.name,
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                          subtitle: Text(
                            "${_tagName(e.tagServerId)}"
                            "${e.isRecurring ? " · recurring" : ""}",
                          ),
                          trailing: Text(
                            formatMoneyLine(b.currency, e.amount),
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                          onTap: () => setState(() {
                            if (open) {
                              _expanded.remove(e.localId);
                            } else {
                              _expanded.add(e.localId);
                            }
                          }),
                        ),
                        if (open)
                          Padding(
                            padding: const EdgeInsets.only(left: 8, bottom: 12),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                for (final s in subs)
                                  Padding(
                                    padding: const EdgeInsets.only(bottom: 4),
                                    child: Text(
                                      "${s.isReturn ? "Return" : "Sub"}: "
                                      "${s.name} · "
                                      "${formatMoneyLine(b.currency, s.amount)}",
                                      style: Theme.of(context)
                                          .textTheme
                                          .bodySmall,
                                    ),
                                  ),
                                Wrap(
                                  spacing: 4,
                                  children: [
                                    TextButton(
                                      onPressed: () async {
                                        await Navigator.of(context).push<bool>(
                                          MaterialPageRoute<bool>(
                                            builder: (_) => ExpenseFormScreen(
                                              budgetLocalId: b.localId,
                                              existing: e,
                                            ),
                                          ),
                                        );
                                        if (mounted) {
                                          await _load();
                                        }
                                      },
                                      child: const Text("Edit"),
                                    ),
                                    TextButton(
                                      onPressed: () async {
                                        await Navigator.of(context).push<bool>(
                                          MaterialPageRoute<bool>(
                                            builder: (_) =>
                                                SubExpenseFormScreen(
                                              expenseLocalId: e.localId,
                                            ),
                                          ),
                                        );
                                        if (mounted) {
                                          await _load();
                                        }
                                      },
                                      child: const Text("Add sub"),
                                    ),
                                    TextButton(
                                      onPressed: () =>
                                          _confirmDeleteExpense(e),
                                      child: const Text("Delete"),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        const Divider(height: 1),
                      ],
                    );
                  }),
                ],
              ),
            ),
      ),
    );
  }
}
