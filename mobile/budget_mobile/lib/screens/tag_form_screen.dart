import "package:flutter/material.dart";

import "../repositories/tag_repository.dart";
import "../theme/minimal_theme.dart";

class TagFormScreen extends StatefulWidget {
  const TagFormScreen({
    super.key,
    required this.repository,
    this.existing,
  });

  final TagRepository repository;
  final TagRow? existing;

  @override
  State<TagFormScreen> createState() => _TagFormScreenState();
}

class _TagFormScreenState extends State<TagFormScreen> {
  final _name = TextEditingController();
  final _desc = TextEditingController();
  final _color = TextEditingController();
  bool _active = true;

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    if (e != null) {
      _name.text = e.name;
      _desc.text = e.description;
      _color.text = e.color;
      _active = e.isActive;
    } else {
      _color.text = "#2196f3";
    }
  }

  @override
  void dispose() {
    _name.dispose();
    _desc.dispose();
    _color.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MinimalPageBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(title: const Text("Tag")),
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
              controller: _color,
              decoration: const InputDecoration(labelText: "Color #RRGGBB"),
            ),
            SwitchListTile(
              title: const Text("Active"),
              value: _active,
              onChanged: (v) => setState(() => _active = v),
            ),
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
                    color: _color.text.trim().isEmpty ? "#2196f3" : _color.text.trim(),
                    isActive: _active,
                  );
                } else {
                  await widget.repository.updateLocal(
                    localId: e.localId,
                    name: n,
                    description: _desc.text.trim(),
                    color: _color.text.trim().isEmpty ? "#2196f3" : _color.text.trim(),
                    isActive: _active,
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
