import "package:flutter_test/flutter_test.dart";
import "package:google_fonts/google_fonts.dart";

import "package:budget_mobile/main.dart";
import "package:budget_mobile/services/mobile_budget_api_client.dart";
import "package:budget_mobile/services/secure_token_store.dart";
import "package:budget_mobile/services/settings_service.dart";
import "package:budget_mobile/services/sync_service.dart";

class _NoopMobileApi extends MobileBudgetApiClient {
  _NoopMobileApi(SettingsService s) : super(s, SecureTokenStore());

  @override
  Future<bool> pingHealth() async => false;
}

void main() {
  setUpAll(() {
    TestWidgetsFlutterBinding.ensureInitialized();
    GoogleFonts.config.allowRuntimeFetching = false;
  });

  testWidgets(
    "shell shows Months tab after load",
    (tester) async {
      final settings = SettingsService.inMemory();
      final api = _NoopMobileApi(settings);
      final sync = SyncService.test(settings: settings, api: api);
      final syncFuture = Future<SyncService>.value(sync);
      await tester.pumpWidget(
        BudgetMobileApp(
          syncServiceFuture: syncFuture,
          homeBudgetCountLoader: () async => 0,
          homeBudgetRepository: null,
          homeBudgetSync: null,
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 50));

      expect(find.text("Months"), findsWidgets);
      expect(find.textContaining("No months yet"), findsOneWidget);
      expect(find.text("More"), findsOneWidget);
    },
    timeout: const Timeout(Duration(seconds: 15)),
  );
}
