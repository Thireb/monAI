import "package:flutter/material.dart";

import "../app_scope.dart";
import "../repositories/budget_repository.dart";
import "../services/budget_sync_service.dart";
import "../services/sync_service.dart";
import "../theme/minimal_theme.dart";
import "../utils/budget_format.dart";
import "budget_detail_screen.dart";
import "budget_form_screen.dart";
import "catalog_categories_screen.dart";
import "catalog_tags_screen.dart";
import "settings_screen.dart";

class HomeScreen extends StatefulWidget {
  const HomeScreen({
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
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _budgetCount = 0;
  List<BudgetRow> _rows = [];
  List<int> _years = [];
  Map<int, List<BudgetRow>> _byYear = {};
  bool _loading = true;
  late Future<SyncService> _syncFuture;

  @override
  void initState() {
    super.initState();
    _syncFuture = widget.syncServiceFuture ??
        Future<SyncService>.value(AppScope.syncService);
    _load();
  }

  Future<void> _load() async {
    final repo = widget.budgetRepository;
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
      _rows = rows;
      _years = years;
      _byYear = byYear;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MinimalPageBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: const Text("monAI"),
          actions: [
            if (widget.budgetRepository != null) ...[
              IconButton(
                icon: const Icon(Icons.category_outlined),
                tooltip: "Categories",
                onPressed: () {
                  Navigator.of(context).push<void>(
                    MaterialPageRoute<void>(
                      builder: (_) => const CatalogCategoriesScreen(),
                    ),
                  );
                },
              ),
              IconButton(
                icon: const Icon(Icons.label_outline),
                tooltip: "Tags",
                onPressed: () {
                  Navigator.of(context).push<void>(
                    MaterialPageRoute<void>(
                      builder: (_) => const CatalogTagsScreen(),
                    ),
                  );
                },
              ),
              IconButton(
                icon: const Icon(Icons.add_circle_outline),
                onPressed: () async {
                  await Navigator.of(context).push<bool>(
                    MaterialPageRoute<bool>(
                      builder: (_) => BudgetFormScreen(
                        repository: widget.budgetRepository!,
                      ),
                    ),
                  );
                  if (mounted) {
                    await _load();
                  }
                },
              ),
            ],
            IconButton(
              icon: const Icon(Icons.settings_outlined),
              onPressed: () async {
                await Navigator.of(context).push<void>(
                  MaterialPageRoute<void>(
                    builder: (_) => const SettingsScreen(),
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
            : ListView(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                children: [
                  Text(
                    "Dashboard",
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: MinimalColors.textPrimary,
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "$_budgetCount budget month(s) stored on this device",
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: MinimalColors.textSecondary,
                        ),
                  ),
                  if (widget.budgetRepository != null && _rows.isNotEmpty) ...[
                    const SizedBox(height: 20),
                    for (final year in _years) ...[
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8, left: 2),
                        child: Text(
                          year > 0 ? "$year" : "Other",
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w600,
                                color: MinimalColors.textPrimary,
                              ),
                        ),
                      ),
                      ...(_byYear[year] ?? []).map((r) {
                        final label = formatBudgetMonthLabel(r.month);
                        return minimalCard(
                          child: ListTile(
                            title: Text(label),
                            subtitle: Text(
                              "${r.income.toStringAsFixed(2)} ${r.currency}"
                              "${r.isArchived ? " · archived" : ""}",
                            ),
                            trailing: r.dirty == 1
                                ? const Icon(Icons.cloud_upload_outlined, size: 20)
                                : const Icon(Icons.chevron_right),
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
                          ),
                        );
                      }),
                    ],
                  ],
                  const SizedBox(height: 24),
                  minimalCard(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "Home sync",
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            "Ping checks the server. Sync pushes categories, tags, "
                            "budgets, expenses; then pulls server updates.",
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: MinimalColors.textSecondary,
                                ),
                          ),
                          const SizedBox(height: 16),
                          FutureBuilder<SyncService>(
                            future: _syncFuture,
                            builder: (context, snap) {
                              if (!snap.hasData) {
                                return const SizedBox(
                                  height: 40,
                                  child: Center(
                                    child: CircularProgressIndicator(),
                                  ),
                                );
                              }
                              final s = snap.data!.settings;
                              final ok = s.lastBackgroundPingOk;
                              final at = s.lastBackgroundPingAt;
                              final status = ok == null
                                  ? "No background ping yet."
                                  : ok
                                      ? "Last ping: OK"
                                      : "Last ping: unreachable";
                              final when = at == null
                                  ? ""
                                  : " (${at.toLocal().toString().split(".").first})";
                              return Text(
                                "$status$when",
                                style: Theme.of(context).textTheme.bodySmall,
                              );
                            },
                          ),
                          const SizedBox(height: 12),
                          FilledButton.icon(
                            onPressed: () async {
                              final sync = await _syncFuture;
                              final ok = await sync.pingNow();
                              if (!context.mounted) {
                                return;
                              }
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(
                                    ok
                                        ? "Home server responded."
                                        : "Could not reach home server (offline is fine).",
                                  ),
                                ),
                              );
                              setState(() {});
                            },
                            icon: const Icon(Icons.wifi_find),
                            label: const Text("Ping home server now"),
                          ),
                          if (widget.budgetSyncService != null) ...[
                            const SizedBox(height: 8),
                            FilledButton.tonalIcon(
                              onPressed: () async {
                                final ok = await widget.budgetSyncService!
                                    .syncAll();
                                if (!context.mounted) {
                                  return;
                                }
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text(
                                      ok
                                          ? "Sync finished."
                                          : "Sync failed (offline or fix Settings).",
                                    ),
                                  ),
                                );
                                await _load();
                              },
                              icon: const Icon(Icons.sync),
                              label: const Text("Sync data now"),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}
