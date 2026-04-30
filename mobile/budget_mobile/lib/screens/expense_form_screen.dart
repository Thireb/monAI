import "package:flutter/material.dart";
import "package:flutter/services.dart";

import "../app_scope.dart";
import "../repositories/category_repository.dart";
import "../repositories/expense_repository.dart";
import "../repositories/tag_repository.dart";
import "../theme/minimal_theme.dart";

class ExpenseFormScreen extends StatefulWidget {
  const ExpenseFormScreen({
    super.key,
    required this.budgetLocalId,
    this.existing,
  });

  final int budgetLocalId;
  final ExpenseRow? existing;

  @override
  State<ExpenseFormScreen> createState() => _ExpenseFormScreenState();
}

class _ExpenseFormScreenState extends State<ExpenseFormScreen> {
  final _name = TextEditingController();
  final _amount = TextEditingController();
  bool _recurring = false;
  int? _categoryServerId;
  int? _tagServerId;

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    if (e != null) {
      _name.text = e.name;
      _amount.text = e.amount.toStringAsFixed(2);
      _recurring = e.isRecurring;
      _categoryServerId = e.categoryServerId;
      _tagServerId = e.tagServerId;
    }
  }

  @override
  void dispose() {
    _name.dispose();
    _amount.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<dynamic>>(
      future: Future.wait<dynamic>([
        AppScope.categoryRepo.listNonDeleted(),
        AppScope.tagRepo.listNonDeleted(),
      ]),
      builder: (context, snap) {
        if (!snap.hasData) {
          return MinimalPageBackground(
            child: Scaffold(
              backgroundColor: Colors.transparent,
              appBar: AppBar(title: const Text("Expense")),
              body: const Center(child: CircularProgressIndicator()),
            ),
          );
        }
        final cats = snap.data![0] as List<CategoryRow>;
        final tags = snap.data![1] as List<TagRow>;
        final withCats = <(int?, String)>[
          (null, "None"),
          ...cats
              .where((c) => c.serverId != null)
              .map((c) => (c.serverId!, c.name)),
        ];
        final withTags = <(int?, String)>[
          (null, "None"),
          ...tags.where((t) => t.serverId != null).map((t) => (t.serverId!, t.name)),
        ];
        return MinimalPageBackground(
          child: Scaffold(
            backgroundColor: Colors.transparent,
            appBar: AppBar(title: const Text("Expense")),
            body: ListView(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
              children: [
                Text(
                  "Category/tag must be synced (have server id) to attach.",
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: MinimalColors.textSecondary,
                        height: 1.4,
                      ),
                ),
                const SizedBox(height: 20),
                TextField(
                  controller: _name,
                  textCapitalization: TextCapitalization.sentences,
                  decoration: const InputDecoration(
                    labelText: "Name",
                    alignLabelWithHint: true,
                  ),
                ),
                const SizedBox(height: 20),
                TextField(
                  controller: _amount,
                  decoration: const InputDecoration(
                    labelText: "Amount",
                    alignLabelWithHint: true,
                  ),
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  inputFormatters: [
                    FilteringTextInputFormatter.allow(RegExp(r"[0-9.]")),
                  ],
                ),
                const SizedBox(height: 8),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text("Recurring"),
                  value: _recurring,
                  onChanged: (v) => setState(() => _recurring = v),
                ),
                const SizedBox(height: 8),
                DropdownButtonFormField<int?>(
                  isExpanded: true,
                  decoration: const InputDecoration(
                    labelText: "Category",
                    alignLabelWithHint: true,
                  ),
                  value: _validSelection(_categoryServerId, withCats),
                  items: withCats
                      .map(
                        (t) => DropdownMenuItem<int?>(
                          value: t.$1,
                          child: Text(t.$2),
                        ),
                      )
                      .toList(),
                  onChanged: (v) => setState(() => _categoryServerId = v),
                ),
                const SizedBox(height: 20),
                DropdownButtonFormField<int?>(
                  isExpanded: true,
                  decoration: const InputDecoration(
                    labelText: "Tag",
                    alignLabelWithHint: true,
                  ),
                  value: _validSelection(_tagServerId, withTags),
                  items: withTags
                      .map(
                        (t) => DropdownMenuItem<int?>(
                          value: t.$1,
                          child: Text(t.$2),
                        ),
                      )
                      .toList(),
                  onChanged: (v) => setState(() => _tagServerId = v),
                ),
                const SizedBox(height: 28),
                FilledButton(
                  onPressed: () async {
                    final n = _name.text.trim();
                    final amt = double.tryParse(_amount.text.trim());
                    if (n.isEmpty || amt == null || amt <= 0) {
                      return;
                    }
                    final e = widget.existing;
                    if (e == null) {
                      await AppScope.expenseRepo.insertLocal(
                        budgetLocalId: widget.budgetLocalId,
                        name: n,
                        amount: amt,
                        isRecurring: _recurring,
                        categoryServerId: _categoryServerId,
                        tagServerId: _tagServerId,
                      );
                    } else {
                      await AppScope.expenseRepo.updateLocal(
                        localId: e.localId,
                        budgetLocalId: widget.budgetLocalId,
                        name: n,
                        amount: amt,
                        isRecurring: _recurring,
                        categoryServerId: _categoryServerId,
                        tagServerId: _tagServerId,
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
      },
    );
  }

  int? _validSelection(int? current, List<(int?, String)> items) {
    if (current == null) {
      return null;
    }
    for (final t in items) {
      if (t.$1 == current) {
        return current;
      }
    }
    return null;
  }
}
