import "package:flutter/material.dart";

import "../repositories/category_repository.dart";
import "../theme/minimal_theme.dart";

class CategoryFormScreen extends StatefulWidget {
  const CategoryFormScreen({
    super.key,
    required this.repository,
    this.existing,
  });

  final CategoryRepository repository;
  final CategoryRow? existing;

  @override
  State<CategoryFormScreen> createState() => _CategoryFormScreenState();
}

class _CategoryFormScreenState extends State<CategoryFormScreen> {
  final _name = TextEditingController();
  final _desc = TextEditingController();
  final _icon = TextEditingController();
  final _color = TextEditingController();

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    if (e != null) {
      _name.text = e.name;
      _desc.text = e.description;
      _icon.text = e.icon;
      _color.text = e.color;
    } else {
      _color.text = "#000000";
    }
  }

  @override
  void dispose() {
    _name.dispose();
    _desc.dispose();
    _icon.dispose();
    _color.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MinimalPageBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(title: const Text("Category")),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextField(
              controller: _name,
              decoration: const InputDecoration(labelText: "Name"),
            ),
            TextField(
              controller: _desc,
              decoration: const InputDecoration(labelText: "Description"),
            ),
            TextField(
              controller: _icon,
              decoration: const InputDecoration(labelText: "Icon (optional)"),
            ),
            TextField(
              controller: _color,
              decoration: const InputDecoration(labelText: "Color #RRGGBB"),
            ),
            const SizedBox(height: 20),
            FilledButton(
              onPressed: () async {
                final n = _name.text.trim();
                if (n.isEmpty) {
                  return;
                }
                final e = widget.existing;
                if (e == null) {
                  await widget.repository.insertLocal(
                    name: n,
                    description: _desc.text.trim(),
                    icon: _icon.text.trim(),
                    color: _color.text.trim().isEmpty ? "#000000" : _color.text.trim(),
                  );
                } else {
                  await widget.repository.updateLocal(
                    localId: e.localId,
                    name: n,
                    description: _desc.text.trim(),
                    icon: _icon.text.trim(),
                    color: _color.text.trim().isEmpty ? "#000000" : _color.text.trim(),
                  );
                }
                if (context.mounted) {
                  Navigator.of(context).pop(true);
                }
              },
              child: const Text("Save locally"),
            ),
          ],
        ),
      ),
    );
  }
}
