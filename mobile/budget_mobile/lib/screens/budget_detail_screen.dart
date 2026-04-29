import "package:flutter/material.dart";

import "../app_scope.dart";
import "../repositories/budget_repository.dart";
import "../repositories/expense_repository.dart";
import "../repositories/sub_expense_repository.dart";
import "../theme/minimal_theme.dart";
import "../utils/budget_format.dart";
import "budget_form_screen.dart";
import "expense_form_screen.dart";
import "sub_expense_form_screen.dart";

class BudgetDetailScreen extends StatefulWidget {
  const BudgetDetailScreen({super.key, required this.budget});

  final BudgetRow budget;

  @override
  State<BudgetDetailScreen> createState() => _BudgetDetailScreenState();
}

class _BudgetDetailScreenState extends State<BudgetDetailScreen> {
  List<ExpenseRow> _expenses = [];
  List<SubExpenseRow> _subAll = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final list = await AppScope.expenseRepo
        .listForBudgetLocalId(widget.budget.localId);
    final subs = await AppScope.subExpenseRepo
        .listForBudgetLocalId(widget.budget.localId);
    if (!mounted) {
      return;
    }
    setState(() {
      _expenses = list;
      _subAll = subs;
      _loading = false;
    });
  }

  List<SubExpenseRow> _subsForExpense(int expenseLocalId) {
    return _subAll.where((s) => s.expenseLocalId == expenseLocalId).toList();
  }

  String _remainingLine(ExpenseRow e) {
    final allocated = e.amount;
    double spent = 0;
    double returns = 0;
    for (final s in _subsForExpense(e.localId)) {
      if (s.isReturn) {
        returns += s.amount;
      } else {
        spent += s.amount;
      }
    }
    final remaining = allocated - spent + returns;
    return "Allocated ${allocated.toStringAsFixed(2)} · "
        "spent ${spent.toStringAsFixed(2)}"
        "${returns > 0 ? " · returns ${returns.toStringAsFixed(2)}" : ""} · "
        "remaining ${remaining.toStringAsFixed(2)}";
  }

  @override
  Widget build(BuildContext context) {
    final b = widget.budget;
    final titleLabel = formatBudgetMonthLabel(b.month);
    return MinimalPageBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: Text(titleLabel),
          actions: [
            IconButton(
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
                if (context.mounted) {
                  await _load();
                }
              },
            ),
          ],
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "${b.income.toStringAsFixed(2)} ${b.currency}",
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        if (b.isArchived) ...[
                          const SizedBox(height: 4),
                          Text(
                            "Archived",
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: MinimalColors.textSecondary,
                                ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Text(
                      "Expenses & sub-lines",
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  Expanded(
                    child: _expenses.isEmpty
                        ? Center(
                            child: Text(
                              "No expenses yet. Tap + to add one.",
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: MinimalColors.textSecondary,
                                  ),
                            ),
                          )
                        : ListView.builder(
                            padding: const EdgeInsets.only(bottom: 88),
                            itemCount: _expenses.length,
                            itemBuilder: (ctx, i) {
                              final e = _expenses[i];
                              final subs = _subsForExpense(e.localId);
                              return minimalCard(
                                child: ExpansionTile(
                                  initiallyExpanded: subs.isNotEmpty,
                                  title: Text(e.name),
                                  subtitle: Text(
                                    "${e.amount.toStringAsFixed(2)}"
                                    "${e.isRecurring ? " · recurring" : ""}\n"
                                    "${_remainingLine(e)}",
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodySmall
                                        ?.copyWith(
                                          color: MinimalColors.textSecondary,
                                        ),
                                  ),
                                  trailing: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      if (e.dirty == 1)
                                        const Padding(
                                          padding: EdgeInsets.only(right: 4),
                                          child: Icon(
                                            Icons.cloud_upload_outlined,
                                            size: 18,
                                          ),
                                        ),
                                      const Icon(Icons.expand_more),
                                    ],
                                  ),
                                  children: [
                                    if (subs.isEmpty)
                                      Padding(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 16,
                                          vertical: 8,
                                        ),
                                        child: Text(
                                          "No sub-expenses yet.",
                                          style: Theme.of(context)
                                              .textTheme
                                              .bodySmall
                                              ?.copyWith(
                                                color: MinimalColors
                                                    .textSecondary,
                                              ),
                                        ),
                                      ),
                                    ...subs.map((s) {
                                      return ListTile(
                                        dense: true,
                                        visualDensity: VisualDensity.compact,
                                        leading: Icon(
                                          s.isReturn
                                              ? Icons.reply
                                              : Icons.subdirectory_arrow_right,
                                          size: 20,
                                          color: s.isReturn
                                              ? MinimalColors.primaryGreen
                                              : MinimalColors.textSecondary,
                                        ),
                                        title: Text(
                                          s.isReturn
                                              ? "Return: ${s.name}"
                                              : s.name,
                                          style: Theme.of(context)
                                              .textTheme
                                              .bodyMedium,
                                        ),
                                        subtitle: Text(
                                          s.amount.toStringAsFixed(2),
                                        ),
                                        trailing: s.dirty == 1
                                            ? const Icon(
                                                Icons.cloud_upload_outlined,
                                                size: 16,
                                              )
                                            : null,
                                        onTap: () async {
                                          await Navigator.of(context)
                                              .push<bool>(
                                            MaterialPageRoute<bool>(
                                              builder: (_) =>
                                                  SubExpenseFormScreen(
                                                expenseLocalId: e.localId,
                                                existing: s,
                                              ),
                                            ),
                                          );
                                          await _load();
                                        },
                                      );
                                    }),
                                    Padding(
                                      padding: const EdgeInsets.fromLTRB(
                                        8,
                                        0,
                                        8,
                                        8,
                                      ),
                                      child: Row(
                                        children: [
                                          TextButton.icon(
                                            onPressed: () async {
                                              await Navigator.of(context)
                                                  .push<bool>(
                                                MaterialPageRoute<bool>(
                                                  builder: (_) =>
                                                      SubExpenseFormScreen(
                                                    expenseLocalId: e.localId,
                                                  ),
                                                ),
                                              );
                                              await _load();
                                            },
                                            icon: const Icon(
                                              Icons.add,
                                              size: 20,
                                            ),
                                            label: const Text("Sub-expense"),
                                          ),
                                          const Spacer(),
                                          TextButton(
                                            onPressed: () async {
                                              await Navigator.of(context)
                                                  .push<bool>(
                                                MaterialPageRoute<bool>(
                                                  builder: (_) =>
                                                      ExpenseFormScreen(
                                                    budgetLocalId: b.localId,
                                                    existing: e,
                                                  ),
                                                ),
                                              );
                                              await _load();
                                            },
                                            child: const Text("Edit expense"),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                ),
                              );
                            },
                          ),
                  ),
                ],
              ),
        floatingActionButton: FloatingActionButton(
          onPressed: () async {
            await Navigator.of(context).push<bool>(
              MaterialPageRoute<bool>(
                builder: (_) => ExpenseFormScreen(budgetLocalId: b.localId),
              ),
            );
            await _load();
          },
          child: const Icon(Icons.add),
        ),
      ),
    );
  }
}
