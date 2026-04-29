import "dart:convert";

import "package:http/http.dart" as http;

import "secure_token_store.dart";
import "settings_service.dart";

/// Authenticated calls to the Django mobile sync API. Returns null / empty on failure.
class MobileBudgetApiClient {
  MobileBudgetApiClient(
    this._settings,
    this._tokens,
  );

  final SettingsService _settings;
  final SecureTokenStore _tokens;

  static const Duration _timeout = Duration(seconds: 30);

  Map<String, String> _jsonHeaders(String? token) {
    final h = <String, String>{"Content-Type": "application/json"};
    if (token != null && token.isNotEmpty) {
      h["Authorization"] = "Token $token";
    }
    return h;
  }

  Uri? _api(String path) {
    final base = _settings.homeBaseUrl;
    if (base == null) {
      return null;
    }
    final n = base.endsWith("/") ? base.substring(0, base.length - 1) : base;
    return Uri.parse("$n$path");
  }

  Uri? _healthUri() {
    return _api("/api/health/");
  }

  /// Server up check (no auth).
  Future<bool> pingHealth() async {
    final uri = _healthUri();
    if (uri == null) {
      return false;
    }
    try {
      final response = await http.get(uri).timeout(_timeout);
      return response.statusCode >= 200 && response.statusCode < 300;
    } on Object {
      return false;
    }
  }

  Future<String?> fetchToken({
    required String email,
    required String password,
  }) async {
    final uri = _api("/api/mobile/auth/token/");
    if (uri == null) {
      return null;
    }
    try {
      final body = jsonEncode({"email": email, "password": password});
      final response = await http
          .post(uri, headers: _jsonHeaders(null), body: body)
          .timeout(_timeout);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        return null;
      }
      final map = jsonDecode(response.body) as Map<String, dynamic>;
      final t = map["token"];
      if (t is! String || t.isEmpty) {
        return null;
      }
      await _tokens.writeToken(t);
      return t;
    } on Object {
      return null;
    }
  }

  Future<Map<String, dynamic>?> pullBudgets(String? updatedAfterIso) async {
    final token = await _tokens.readToken();
    if (token == null || token.isEmpty) {
      return null;
    }
    final base = _api("/api/mobile/budgets/pull/");
    if (base == null) {
      return null;
    }
    final uri = updatedAfterIso != null && updatedAfterIso.isNotEmpty
        ? base.replace(queryParameters: {"updated_after": updatedAfterIso})
        : base;
    try {
      final response = await http
          .get(uri, headers: _jsonHeaders(token))
          .timeout(_timeout);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        return null;
      }
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on Object {
      return null;
    }
  }

  Future<Map<String, dynamic>?> pushBudgets(List<Map<String, dynamic>> budgets) async {
    final token = await _tokens.readToken();
    if (token == null || token.isEmpty) {
      return null;
    }
    final uri = _api("/api/mobile/budgets/push/");
    if (uri == null) {
      return null;
    }
    try {
      final body = jsonEncode({"budgets": budgets});
      final response = await http
          .post(uri, headers: _jsonHeaders(token), body: body)
          .timeout(_timeout);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        return null;
      }
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on Object {
      return null;
    }
  }
}
