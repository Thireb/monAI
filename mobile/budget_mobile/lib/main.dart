import "package:flutter/material.dart";

import "app_bootstrap.dart";
import "app_scope.dart";
import "repositories/budget_repository.dart";
import "screens/main_shell.dart";
import "services/budget_sync_service.dart";
import "services/sync_service.dart";
import "theme/minimal_theme.dart";

Future<void> main() async {
  await bootstrapApp(registerBackgroundSync: true);
  runApp(const BudgetMobileApp());
}

class BudgetMobileApp extends StatelessWidget {
  const BudgetMobileApp({
    super.key,
    this.syncServiceFuture,
    this.homeBudgetCountLoader,
    this.homeBudgetRepository,
    this.homeBudgetSync,
  });

  /// Injected in tests.
  final Future<SyncService>? syncServiceFuture;

  final Future<int> Function()? homeBudgetCountLoader;

  final BudgetRepository? homeBudgetRepository;

  final BudgetSyncService? homeBudgetSync;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "monAI Budget",
      debugShowCheckedModeBanner: false,
      theme: buildMinimalTheme(),
      home: MainShell(
        syncServiceFuture: syncServiceFuture,
        budgetCountLoader: homeBudgetCountLoader,
        budgetRepository: homeBudgetCountLoader != null
            ? homeBudgetRepository
            : (homeBudgetRepository ?? AppScope.budgetRepo),
        budgetSyncService: homeBudgetCountLoader != null
            ? homeBudgetSync
            : (homeBudgetSync ?? AppScope.budgetSync),
      ),
    );
  }
}
