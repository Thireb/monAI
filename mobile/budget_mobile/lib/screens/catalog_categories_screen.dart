import "package:flutter/material.dart";

import "../app_scope.dart";
import "../repositories/category_repository.dart";
import "category_form_screen.dart";

class CatalogCategoriesScreen extends StatefulWidget {
  const CatalogCategoriesScreen({super.key});

  @override
  State<CatalogCategoriesScreen> createState() => _CatalogCategoriesScreenState();
}

class _CatalogCategoriesScreenState extends State<CatalogCategoriesScreen> {
  List<CategoryRow> _rows = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final rows = await AppScope.categoryRepo.listNonDeleted();
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
      appBar: AppBar(title: const Text("Categories")),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
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
                        builder: (_) => CategoryFormScreen(
                          repository: AppScope.categoryRepo,
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
              builder: (_) => CategoryFormScreen(
                repository: AppScope.categoryRepo,
              ),
            ),
          );
          await _load();
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}
