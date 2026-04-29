import "package:flutter/widgets.dart";
import "package:workmanager/workmanager.dart";

import "package:budget_mobile/app_bootstrap.dart";
import "package:budget_mobile/app_scope.dart";

const String kPeriodicSyncTaskName = "com.monai.budget.sync";
const String kUniquePeriodicName = "home-server-periodic-sync";

@pragma("vm:entry-point")
void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    WidgetsFlutterBinding.ensureInitialized();
    try {
      await bootstrapApp(registerBackgroundSync: false);
      await AppScope.syncService.runBackgroundPing();
      await AppScope.budgetSync.syncAll();
    } on Object {
      // Never fail the worker; WorkManager will reschedule per policy.
    }
    return Future.value(true);
  });
}

/// Registers periodic background work (minimum interval ~15 minutes on Android).
class BackgroundSync {
  BackgroundSync._();

  static Future<void> register() async {
    await Workmanager().initialize(callbackDispatcher);
    await Workmanager().registerPeriodicTask(
      kUniquePeriodicName,
      kPeriodicSyncTaskName,
      frequency: const Duration(minutes: 15),
      constraints: Constraints(
        networkType: NetworkType.connected,
      ),
    );
  }
}
