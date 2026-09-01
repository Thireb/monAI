import "package:flutter/material.dart";

import "../app_scope.dart";
import "../services/budget_sync_service.dart";
import "../services/sync_service.dart";
import "../theme/minimal_theme.dart";
import "catalog_categories_screen.dart";
import "catalog_tags_screen.dart";
import "settings_screen.dart";

/// Categories, tags (accounts), settings, and sync actions.
class MoreScreen extends StatefulWidget {
  const MoreScreen({
    super.key,
    this.syncServiceFuture,
    this.budgetSyncService,
  });

  final Future<SyncService>? syncServiceFuture;
  final BudgetSyncService? budgetSyncService;

  @override
  State<MoreScreen> createState() => _MoreScreenState();
}

class _MoreScreenState extends State<MoreScreen> {
  late Future<SyncService> _syncFuture;

  @override
  void initState() {
    super.initState();
    _syncFuture = widget.syncServiceFuture ??
        Future<SyncService>.value(AppScope.syncService);
  }

  BudgetSyncService? get _budgetSync =>
      widget.budgetSyncService ?? AppScope.budgetSync;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: const Text("More")),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 32),
        children: [
          ListTile(
            leading: const Icon(Icons.category_outlined),
            title: const Text("Categories"),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              Navigator.of(context).push<void>(
                MaterialPageRoute<void>(
                  builder: (_) => const CatalogCategoriesScreen(),
                ),
              );
            },
          ),
          ListTile(
            leading: const Icon(Icons.account_balance_wallet_outlined),
            title: const Text("Accounts (tags)"),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              Navigator.of(context).push<void>(
                MaterialPageRoute<void>(
                  builder: (_) => const CatalogTagsScreen(),
                ),
              );
            },
          ),
          ListTile(
            leading: const Icon(Icons.settings_outlined),
            title: const Text("Settings"),
            subtitle: const Text("Server URL and sign-in"),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              Navigator.of(context).push<void>(
                MaterialPageRoute<void>(
                  builder: (_) => const SettingsScreen(),
                ),
              );
            },
          ),
          const SizedBox(height: 16),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              "Sync",
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    color: MinimalColors.textSecondary,
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ),
          const SizedBox(height: 8),
          FutureBuilder<SyncService>(
            future: _syncFuture,
            builder: (context, snap) {
              if (!snap.hasData) {
                return const Padding(
                  padding: EdgeInsets.all(16),
                  child: LinearProgressIndicator(),
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
              return ListTile(
                title: Text("$status$when"),
                subtitle: const Text(
                  "Push local changes, then pull server updates.",
                ),
              );
            },
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.tonalIcon(
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
                              : "Could not reach home server.",
                        ),
                      ),
                    );
                    setState(() {});
                  },
                  icon: const Icon(Icons.wifi_find),
                  label: const Text("Ping"),
                ),
                FilledButton.icon(
                  onPressed: () async {
                    final ok = await _budgetSync!.syncAll();
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
                    setState(() {});
                  },
                  icon: const Icon(Icons.sync),
                  label: const Text("Sync now"),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
