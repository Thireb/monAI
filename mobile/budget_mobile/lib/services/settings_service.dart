import "package:shared_preferences/shared_preferences.dart";

const String kHomeBaseUrl = "home_base_url";
const String kLastBackgroundPingOk = "last_background_ping_ok";
const String kLastBackgroundPingAt = "last_background_ping_at";

/// Persistent settings backed by [SharedPreferences], or an in-memory map for tests.
///
/// Use [SettingsService.inMemory] in widget/unit tests to avoid platform channels
/// (SharedPreferences.getInstance can hang on headless/CI test bindings).
class SettingsService {
  SettingsService._(this._prefs, this._memory);

  final SharedPreferences? _prefs;
  final Map<String, Object>? _memory;

  static Future<SettingsService> create() async {
    final prefs = await SharedPreferences.getInstance();
    return SettingsService._(prefs, null);
  }

  /// Synchronous, no platform channels — safe for `flutter test`.
  factory SettingsService.inMemory([Map<String, Object>? seed]) {
    return SettingsService._(null, Map<String, Object>.from(seed ?? {}));
  }

  String? get homeBaseUrl {
    if (_memory != null) {
      final v = _memory[kHomeBaseUrl];
      if (v == null || v.toString().trim().isEmpty) {
        return null;
      }
      return v.toString().trim().replaceAll(RegExp(r"/+$"), "");
    }
    assert(_prefs != null);
    final v = _prefs!.getString(kHomeBaseUrl);
    if (v == null || v.trim().isEmpty) {
      return null;
    }
    return v.trim().replaceAll(RegExp(r"/+$"), "");
  }

  Future<void> setHomeBaseUrl(String? url) async {
    if (_memory != null) {
      if (url == null || url.trim().isEmpty) {
        _memory.remove(kHomeBaseUrl);
        return;
      }
      _memory[kHomeBaseUrl] =
          url.trim().replaceAll(RegExp(r"/+$"), "");
      return;
    }
    assert(_prefs != null);
    if (url == null || url.trim().isEmpty) {
      await _prefs!.remove(kHomeBaseUrl);
      return;
    }
    await _prefs!.setString(
      kHomeBaseUrl,
      url.trim().replaceAll(RegExp(r"/+$"), ""),
    );
  }

  Future<void> setLastBackgroundPing({required bool ok}) async {
    if (_memory != null) {
      _memory[kLastBackgroundPingOk] = ok;
      _memory[kLastBackgroundPingAt] = DateTime.now().millisecondsSinceEpoch;
      return;
    }
    final prefs = _prefs!;
    await prefs.setBool(kLastBackgroundPingOk, ok);
    await prefs.setInt(
      kLastBackgroundPingAt,
      DateTime.now().millisecondsSinceEpoch,
    );
  }

  bool? get lastBackgroundPingOk {
    if (_memory != null) {
      final v = _memory[kLastBackgroundPingOk];
      return v is bool ? v : null;
    }
    return _prefs!.getBool(kLastBackgroundPingOk);
  }

  DateTime? get lastBackgroundPingAt {
    if (_memory != null) {
      final v = _memory[kLastBackgroundPingAt];
      if (v is int) {
        return DateTime.fromMillisecondsSinceEpoch(v);
      }
      return null;
    }
    final ms = _prefs!.getInt(kLastBackgroundPingAt);
    if (ms == null) {
      return null;
    }
    return DateTime.fromMillisecondsSinceEpoch(ms);
  }
}
