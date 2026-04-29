import "package:flutter/widgets.dart";

import "app_scope.dart";
import "background/sync_worker.dart";
import "database/app_database.dart";

/// Shared startup for `main()` and background isolate.
///
/// [registerBackgroundSync] false for widget tests and inside WorkManager
/// callback (re-registration must not run from background isolate).
Future<void> bootstrapApp({bool registerBackgroundSync = true}) async {
  WidgetsFlutterBinding.ensureInitialized();
  await AppDatabase.instance.database;
  await AppScope.init();
  if (!registerBackgroundSync) {
    return;
  }
  try {
    await BackgroundSync.register();
  } on Object {
    // WorkManager can fail on emulators or unusual configs; app stays usable.
  }
}
