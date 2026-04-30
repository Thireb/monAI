import "package:flutter/material.dart";

import "../app_scope.dart";
import "../repositories/budget_repository.dart";
import "../repositories/expense_repository.dart";
import "../repositories/sub_expense_repository.dart";
import "../repositories/tag_repository.dart";
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
  List<TagRow> _tags = [];
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
    final tags = await AppScope.tagRepo.listNonDeleted();
    if (!mounted) {
      return;
    }
    setState(() {
      _expenses = list;
      _subAll = subs;
      _tags = tags;
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
    final b = widget.budget;
    return "Allocated ${formatMoneyLine(b.currency, allocated)} · "
        "spent ${formatMoneyLine(b.currency, spent)}"
        "${returns > 0 ? " · returns ${formatMoneyLine(b.currency, returns)}" : ""} · "
        "remaining ${formatMoneyLine(b.currency, remaining)}";
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

  /// Same rule as server [Budget.get_remaining_budget]: income - expenses + returns.
  double _remainingBudget() {
    final b = widget.budget;
    return b.income - _totalExpenseAllocated() + _totalReturnsAll();
  }

  /// Per-tag sums of allocated expense amounts (matches web "Account Breakdown").
  List<({String name, String colorHex, double amount})> _accountBreakdownRows() {
    final byServerId = <int, TagRow>{};
    for (final t in _tags) {
      final sid = t.serverId;
      if (sid != null) {
        byServerId[sid] = t;
      }
    }
    final totals = <String, ({double amount, String color})>{};
    for (final e in _expenses) {
      final tid = e.tagServerId;
      if (tid == null) {
        continue;
      }
      final tag = byServerId[tid];
      final name = tag?.name ?? "Tag #$tid";
      final color = tag?.color ?? "#2196f3";
      final prev = totals[name];
      if (prev == null) {
        totals[name] = (amount: e.amount, color: color);
      } else {
        totals[name] = (
          amount: prev.amount + e.amount,
          color: prev.color,
        );
      }
    }
    final list = totals.entries
        .where((e) => e.value.amount > 0)
        .map(
          (e) => (
            name: e.key,
            colorHex: e.value.color,
            amount: e.value.amount,
          ),
        )
        .toList();
    list.sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
    return list;
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

  Widget _summaryCard({
    required BuildContext context,
    required String label,
    required String valueLine,
    Widget? footer,
  }) {
    final labelStyle = Theme.of(context).textTheme.labelLarge?.copyWith(
          color: MinimalColors.primaryBlue,
          fontWeight: FontWeight.w600,
        );
    final valueStyle = Theme.of(context).textTheme.titleMedium?.copyWith(
          fontWeight: FontWeight.bold,
          color: MinimalColors.textPrimary,
        );
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label, style: labelStyle, textAlign: TextAlign.center),
          const SizedBox(height: 6),
          Text(valueLine, style: valueStyle, textAlign: TextAlign.center),
          if (footer != null) ...[
            const SizedBox(height: 6),
            footer,
          ],
        ],
      ),
    );
  }

  Widget _accountBreakdownSection(BuildContext context, BudgetRow b) {
    final rows = _accountBreakdownRows();
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            "Account Breakdown",
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  color: MinimalColors.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
          ),
          const SizedBox(height: 12),
          if (rows.isEmpty)
            Text(
              "No account breakdown available.",
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: MinimalColors.textSecondary,
                  ),
            )
          else
            Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.center,
              children: rows.map((row) {
                final accent = _parseHexColor(row.colorHex);
                return Container(
                  constraints: const BoxConstraints(minWidth: 140),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: MinimalColors.surfaceGlass,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        row.name.toUpperCase(),
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.labelMedium?.copyWith(
                              color: MinimalColors.textPrimary,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 0.4,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        formatMoneyLine(b.currency, row.amount),
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                              color: accent,
                              fontWeight: FontWeight.w600,
                            ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final b = widget.budget;
    final titleLabel = formatBudgetMonthLabel(b.month);
    final totalExpenses = _totalExpenseAllocated();
    final remaining = _remainingBudget();
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
            : CustomScrollView(
                slivers: [
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                      child: minimalCard(
                        child: Padding(
                          padding: const EdgeInsets.symmetric(
                            vertical: 14,
                            horizontal: 8,
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              if (b.isArchived)
                                Padding(
                                  padding: const EdgeInsets.only(bottom: 10),
                                  child: Text(
                                    "Archived",
                                    textAlign: TextAlign.center,
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodySmall
                                        ?.copyWith(
                                          color: MinimalColors.textSecondary,
                                        ),
                                  ),
                                ),
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Expanded(
                                    child: _summaryCard(
                                      context: context,
                                      label: "Income",
                                      valueLine: formatMoneyLine(
                                        b.currency,
                                        b.income,
                                      ),
                                      footer: TextButton(
                                        onPressed: () async {
                                          await Navigator.of(context)
                                              .push<bool>(
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
                                        child: const Text("Edit"),
                                      ),
                                    ),
                                  ),
                                  Expanded(
                                    child: _summaryCard(
                                      context: context,
                                      label: "Expenses",
                                      valueLine: formatMoneyLine(
                                        b.currency,
                                        totalExpenses,
                                      ),
                                    ),
                                  ),
                                  Expanded(
                                    child: _summaryCard(
                                      context: context,
                                      label: "Remaining",
                                      valueLine: formatMoneyLine(
                                        b.currency,
                                        remaining,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: _accountBreakdownSection(context, b),
                  ),
                  SliverPadding(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
                    sliver: SliverToBoxAdapter(
                      child: Text(
                        "Expenses & sub-lines",
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ),
                  ),
                  if (_expenses.isEmpty)
                    SliverFillRemaining(
                      hasScrollBody: false,
                      child: Center(
                        child: Text(
                          "No expenses yet. Tap + to add one.",
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: MinimalColors.textSecondary,
                              ),
                        ),
                      ),
                    )
                  else
                    SliverPadding(
                      padding: const EdgeInsets.only(bottom: 88),
                      sliver: SliverList(
                        delegate: SliverChildBuilderDelegate(
                          (ctx, i) {
                            final e = _expenses[i];
                            final subs = _subsForExpense(e.localId);
                            return minimalCard(
                              child: ExpansionTile(
                                initiallyExpanded: subs.isNotEmpty,
                                title: Text(e.name),
                                subtitle: Text(
                                  "${formatMoneyLine(b.currency, e.amount)}"
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
                                        formatMoneyLine(b.currency, s.amount),
                                      ),
                                      trailing: s.dirty == 1
                                          ? const Icon(
                                              Icons.cloud_upload_outlined,
                                              size: 16,
                                            )
                                          : null,
                                      onTap: () async {
                                        await Navigator.of(context).push<bool>(
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
                          childCount: _expenses.length,
                        ),
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
