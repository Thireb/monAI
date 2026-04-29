import "package:flutter_secure_storage/flutter_secure_storage.dart";

const String _kAuthTokenKey = "mobile_api_token";

/// Stores the DRF token outside SharedPreferences (encrypted on supported platforms).
class SecureTokenStore {
  SecureTokenStore({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  Future<String?> readToken() => _storage.read(key: _kAuthTokenKey);

  Future<void> writeToken(String? token) async {
    if (token == null || token.isEmpty) {
      await _storage.delete(key: _kAuthTokenKey);
      return;
    }
    await _storage.write(key: _kAuthTokenKey, value: token);
  }
}
