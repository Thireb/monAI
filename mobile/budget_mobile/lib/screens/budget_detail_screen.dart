import "package:flutter/material.dart";

import "../app_scope.dart";
import "../repositories/budget_repository.dart";
import "../repositories/expense_repository.dart";
import "../theme/minimal_theme.dart";
import "budget_form_screen.dart";
import "expense_form_screen.dart";

class BudgetDetailScreen extends StatefulWidget {
  const BudgetDetailScreen({super.key, required this.budget});

  final BudgetRow budget;

  @override
  State<BudgetDetailScreen> createState() => _BudgetDetailScreenState();
}

class _BudgetDetailScreenState extends State<BudgetDetailScreen> {
  List<ExpenseRow> _expenses = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final list = await AppScope.expenseRepo
        .listForBudgetLocalId(widget.budget.localId);
    if (!mounted) {
      return;
    }
    setState(() {
      _expenses = list;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final b = widget.budget;
    return MinimalPageBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: Text(b.month),
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
                    padding: const EdgeInsets.all(16),
                    child: Text(
                      "${b.income.toStringAsFixed(2)} ${b.currency}",
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Text(
                      "Expenses",
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  Expanded(
                    child: ListView.builder(
                      itemCount: _expenses.length,
                      itemBuilder: (ctx, i) {
                        final e = _expenses[i];
                        return ListTile(
                          title: Text(e.name),
                          subtitle: Text(e.amount.toStringAsFixed(2)),
                          trailing: e.dirty == 1
                              ? const Icon(Icons.cloud_upload_outlined, size: 18)
                              : null,
                          onTap: () async {
                            await Navigator.of(context).push<bool>(
                              MaterialPageRoute<bool>(
                                builder: (_) => ExpenseFormScreen(
                                  budgetLocalId: b.localId,
                                  existing: e,
                                ),
                              ),
                            );
                            await _load();
                          },
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
