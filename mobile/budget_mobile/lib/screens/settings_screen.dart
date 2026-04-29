import "package:flutter/material.dart";

import "../app_scope.dart";
import "../theme/minimal_theme.dart";

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _urlController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _hasToken = false;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final url = AppScope.settings.homeBaseUrl ?? "";
    _urlController.text = url;
    final t = await AppScope.tokens.readToken();
    if (!mounted) {
      return;
    }
    setState(() => _hasToken = t != null && t.isNotEmpty);
  }

  @override
  void dispose() {
    _urlController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MinimalPageBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: const Text("Settings"),
        ),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              "Home server URL",
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              "Run Django with LAN bind, e.g. python manage.py runserver 0.0.0.0:8000",
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: MinimalColors.textSecondary,
                  ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _urlController,
              keyboardType: TextInputType.url,
              autocorrect: false,
              decoration: const InputDecoration(
                labelText: "Base URL",
                hintText: "http://192.168.1.10:8000",
              ),
            ),
            const SizedBox(height: 24),
            Text(
              "Sign in (same email/password as the website)",
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _emailController,
              keyboardType: TextInputType.emailAddress,
              autocorrect: false,
              decoration: const InputDecoration(
                labelText: "Email",
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _passwordController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: "Password",
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _hasToken ? "API token saved on device." : "No API token yet.",
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _busy
                  ? null
                  : () async {
                      setState(() => _busy = true);
                      final urlText = _urlController.text.trim();
                      await AppScope.settings.setHomeBaseUrl(
                        urlText.isEmpty ? null : urlText,
                      );
                      final email = _emailController.text.trim();
                      final pass = _passwordController.text;
                      final tok = await AppScope.mobileApi.fetchToken(
                        email: email,
                        password: pass,
                      );
                      if (!context.mounted) {
                        return;
                      }
                      setState(() => _busy = false);
                      if (tok != null) {
                        setState(() => _hasToken = true);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text("Signed in.")),
                        );
                      } else {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text(
                              "Could not sign in. Check URL, email, and password.",
                            ),
                          ),
                        );
                      }
                    },
              child: const Text("Save URL & sign in"),
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: _busy
                  ? null
                  : () async {
                      await AppScope.tokens.writeToken(null);
                      if (!context.mounted) {
                        return;
                      }
                      setState(() => _hasToken = false);
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text("Signed out on this device.")),
                      );
                    },
              child: const Text("Sign out (clear token)"),
            ),
            const SizedBox(height: 24),
            Text(
              "Run: .venv/bin/python manage.py migrate (adds authtoken tables).",
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: MinimalColors.textSecondary,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}
