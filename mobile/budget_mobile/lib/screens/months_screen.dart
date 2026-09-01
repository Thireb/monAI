import "package:flutter/material.dart";

import "../app_scope.dart";
import "../repositories/budget_repository.dart";
import "../services/budget_sync_service.dart";
import "../services/sync_service.dart";
import "../theme/minimal_theme.dart";
import "../utils/budget_format.dart";
import "budget_detail_screen.dart";
import "budget_form_screen.dart";

/// Year-grouped budget months (no sync chrome).
class MonthsScreen extends StatefulWidget {
  const MonthsScreen({
    super.key,
    this.syncServiceFuture,
    this.budgetCountLoader,
    this.budgetRepository,
    this.budgetSyncService,
  });

  final Future<SyncService>? syncServiceFuture;
  final Future<int> Function()? budgetCountLoader;
  final BudgetRepository? budgetRepository;
  final BudgetSyncService? budgetSyncService;

  @override
  State<MonthsScreen> createState() => _MonthsScreenState();
}

class _MonthsScreenState extends State<MonthsScreen> {
  int _budgetCount = 0;
  List<int> _years = [];
  Map<int, List<BudgetRow>> _byYear = {};
  bool _loading = true;

  BudgetRepository? get _repo =>
      widget.budgetRepository ??
      (widget.budgetCountLoader != null ? null : AppScope.budgetRepo);

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final repo = _repo;
    final count = widget.budgetCountLoader != null
        ? await widget.budgetCountLoader!()
        : await (repo?.countNonDeleted() ?? Future.value(0));
    final rows = repo != null ? await repo.listNonDeleted() : <BudgetRow>[];
    final byYear = <int, List<BudgetRow>>{};
    for (final r in rows) {
      final d = parseBudgetMonth(r.month);
      final y = d?.year ?? 0;
      byYear.putIfAbsent(y, () => []).add(r);
    }
    final years = byYear.keys.toList()..sort((a, b) => b.compareTo(a));
    if (!mounted) {
      return;
    }
    setState(() {
      _budgetCount = count;
      _years = years;
      _byYear = byYear;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final repo = _repo;
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text("Months"),
        actions: [
          if (repo != null)
            IconButton(
              icon: const Icon(Icons.add),
              tooltip: "New budget",
              onPressed: () async {
                await Navigator.of(context).push<bool>(
                  MaterialPageRoute<bool>(
                    builder: (_) => BudgetFormScreen(repository: repo),
                  ),
                );
                if (mounted) {
                  await _load();
                }
              },
            ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
                children: [
                  Text(
                    _budgetCount == 0
                        ? "No months yet"
                        : "$_budgetCount month${_budgetCount == 1 ? "" : "s"}",
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    "Open a month to add expenses or transfer between accounts.",
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: MinimalColors.textSecondary,
                        ),
                  ),
                  if (repo != null && _years.isEmpty) ...[
                    const SizedBox(height: 32),
                    FilledButton(
                      onPressed: () async {
                        await Navigator.of(context).push<bool>(
                          MaterialPageRoute<bool>(
                            builder: (_) => BudgetFormScreen(repository: repo),
                          ),
                        );
                        if (mounted) {
                          await _load();
                        }
                      },
                      child: const Text("Create first budget"),
                    ),
                  ],
                  if (repo != null)
                    for (final year in _years) ...[
                      const SizedBox(height: 20),
                      Text(
                        year > 0 ? "$year" : "Other",
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                              color: MinimalColors.textSecondary,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 0.4,
                            ),
                      ),
                      const SizedBox(height: 8),
                      ...(_byYear[year] ?? []).map((r) {
                        final label = formatBudgetMonthLabel(r.month);
                        return InkWell(
                          borderRadius: BorderRadius.circular(12),
                          onTap: () async {
                            await Navigator.of(context).push<bool>(
                              MaterialPageRoute<bool>(
                                builder: (_) => BudgetDetailScreen(budget: r),
                              ),
                            );
                            if (mounted) {
                              await _load();
                            }
                          },
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            child: Row(
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        label,
                                        style: Theme.of(context)
                                            .textTheme
                                            .titleMedium
                                            ?.copyWith(
                                              fontWeight: FontWeight.w600,
                                            ),
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        "${r.income.toStringAsFixed(2)} ${r.currency}"
                                        "${r.isArchived ? " · archived" : ""}",
                                        style: Theme.of(context)
                                            .textTheme
                                            .bodySmall
                                            ?.copyWith(
                                              color:
                                                  MinimalColors.textSecondary,
                                            ),
                                      ),
                                    ],
                                  ),
                                ),
                                if (r.dirty == 1)
                                  const Padding(
                                    padding: EdgeInsets.only(right: 8),
                                    child: Icon(
                                      Icons.cloud_upload_outlined,
                                      size: 18,
                                    ),
                                  ),
                                const Icon(Icons.chevron_right),
                              ],
                            ),
                          ),
                        );
                      }),
                    ],
                ],
              ),
            ),
    );
  }
}
