import "package:flutter/material.dart";

import "../screens/months_screen.dart";
import "../screens/more_screen.dart";
import "../services/budget_sync_service.dart";
import "../services/sync_service.dart";
import "../repositories/budget_repository.dart";
import "../theme/minimal_theme.dart";

/// Root shell with Months / More bottom navigation.
class MainShell extends StatefulWidget {
  const MainShell({
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
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    return MinimalPageBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: IndexedStack(
          index: _index,
          children: [
            MonthsScreen(
              syncServiceFuture: widget.syncServiceFuture,
              budgetCountLoader: widget.budgetCountLoader,
              budgetRepository: widget.budgetRepository,
              budgetSyncService: widget.budgetSyncService,
            ),
            MoreScreen(
              syncServiceFuture: widget.syncServiceFuture,
              budgetSyncService: widget.budgetSyncService,
            ),
          ],
        ),
        bottomNavigationBar: NavigationBar(
          selectedIndex: _index,
          onDestinationSelected: (i) => setState(() => _index = i),
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.calendar_month_outlined),
              selectedIcon: Icon(Icons.calendar_month),
              label: "Months",
            ),
            NavigationDestination(
              icon: Icon(Icons.more_horiz),
              selectedIcon: Icon(Icons.more_horiz),
              label: "More",
            ),
          ],
        ),
      ),
    );
  }
}
