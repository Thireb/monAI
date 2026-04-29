import "package:flutter_test/flutter_test.dart";

import "package:budget_mobile/services/settings_service.dart";

void main() {
  group("SettingsService.inMemory", () {
    test("persists home URL without platform channels", () async {
      final s = SettingsService.inMemory();
      expect(s.homeBaseUrl, isNull);

      await s.setHomeBaseUrl("http://192.168.1.1:8000/");
      expect(s.homeBaseUrl, "http://192.168.1.1:8000");

      await s.setLastBackgroundPing(ok: true);
      expect(s.lastBackgroundPingOk, isTrue);
      expect(s.lastBackgroundPingAt, isNotNull);
    });
  });
}
