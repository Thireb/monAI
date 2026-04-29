import "package:flutter/material.dart";

import "../app_scope.dart";
import "../repositories/budget_repository.dart";
import "../services/budget_sync_service.dart";
import "../services/sync_service.dart";
import "../theme/minimal_theme.dart";
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
    if (!mounted) {
      return;
    }
    setState(() {
      _budgetCount = count;
      _rows = rows;
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
                    "Budget (offline)",
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: MinimalColors.textPrimary,
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "Local budgets: $_budgetCount",
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: MinimalColors.textSecondary,
                        ),
                  ),
                  if (widget.budgetRepository != null && _rows.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    ..._rows.map((r) {
                      return Card(
                        child: ListTile(
                          title: Text(r.month),
                          subtitle: Text(
                            "${r.income.toStringAsFixed(2)} ${r.currency}",
                          ),
                          trailing: r.dirty == 1
                              ? const Icon(Icons.cloud_upload_outlined, size: 20)
                              : null,
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
                  const SizedBox(height: 24),
                  Card(
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
