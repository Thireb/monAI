import "mobile_budget_api_client.dart";
import "settings_service.dart";

/// Coordinates background-safe checks and exposes settings.
class SyncService {
  SyncService(this._settings, this._api);

  final SettingsService _settings;
  final MobileBudgetApiClient _api;

  /// For tests: supply in-memory settings and API (e.g. mock client).
  factory SyncService.test({
    required SettingsService settings,
    required MobileBudgetApiClient api,
  }) {
    return SyncService(settings, api);
  }

  SettingsService get settings => _settings;

  MobileBudgetApiClient get api => _api;

  Future<void> runBackgroundPing() async {
    try {
      final ok = await _api.pingHealth();
      await _settings.setLastBackgroundPing(ok: ok);
    } on Object {
      await _settings.setLastBackgroundPing(ok: false);
    }
  }

  Future<bool> pingNow() async {
    try {
      final ok = await _api.pingHealth();
      await _settings.setLastBackgroundPing(ok: ok);
      return ok;
    } on Object {
      await _settings.setLastBackgroundPing(ok: false);
      return false;
    }
  }
}
