import "package:flutter/material.dart";

import "../app_scope.dart";
import "../repositories/tag_repository.dart";
import "tag_form_screen.dart";

class CatalogTagsScreen extends StatefulWidget {
  const CatalogTagsScreen({super.key});

  @override
  State<CatalogTagsScreen> createState() => _CatalogTagsScreenState();
}

class _CatalogTagsScreenState extends State<CatalogTagsScreen> {
  List<TagRow> _rows = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final rows = await AppScope.tagRepo.listNonDeleted();
    if (!mounted) {
      return;
    }
    setState(() {
      _rows = rows;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Accounts")),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _rows.isEmpty
              ? const Center(child: Text("No accounts yet. Tap + to add."))
              : ListView.builder(
              itemCount: _rows.length,
              itemBuilder: (ctx, i) {
                final r = _rows[i];
                return ListTile(
                  title: Text(r.name),
                  subtitle: Text(r.color),
                  trailing: r.dirty == 1
                      ? const Icon(Icons.cloud_upload_outlined, size: 20)
                      : null,
                  onTap: () async {
                    await Navigator.of(context).push<bool>(
                      MaterialPageRoute<bool>(
                        builder: (_) => TagFormScreen(
                          repository: AppScope.tagRepo,
                          existing: r,
                        ),
                      ),
                    );
                    await _load();
                  },
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          await Navigator.of(context).push<bool>(
            MaterialPageRoute<bool>(
              builder: (_) => TagFormScreen(repository: AppScope.tagRepo),
            ),
          );
          await _load();
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}
