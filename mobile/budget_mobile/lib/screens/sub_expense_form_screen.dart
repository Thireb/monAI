import "package:flutter/material.dart";
import "package:flutter/services.dart";

import "../app_scope.dart";
import "../repositories/sub_expense_repository.dart";
import "../theme/minimal_theme.dart";

class SubExpenseFormScreen extends StatefulWidget {
  const SubExpenseFormScreen({
    super.key,
    required this.expenseLocalId,
    this.existing,
  });

  final int expenseLocalId;
  final SubExpenseRow? existing;

  @override
  State<SubExpenseFormScreen> createState() => _SubExpenseFormScreenState();
}

class _SubExpenseFormScreenState extends State<SubExpenseFormScreen> {
  final _name = TextEditingController();
  final _amount = TextEditingController();
  bool _isReturn = false;

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    if (e != null) {
      _name.text = e.name;
      _amount.text = e.amount.toStringAsFixed(2);
      _isReturn = e.isReturn;
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
    return MinimalPageBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: Text(
            widget.existing == null ? "Add sub-expense" : "Edit sub-expense",
          ),
        ),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextField(
              controller: _name,
              decoration: const InputDecoration(
                labelText: "Name",
                hintText: "e.g. Installment 1",
              ),
              textCapitalization: TextCapitalization.sentences,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _amount,
              decoration: const InputDecoration(
                labelText: "Amount",
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
              title: const Text("Return / refund"),
              subtitle: Text(
                "Marks this line as money coming back toward the budget.",
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: MinimalColors.textSecondary,
                    ),
              ),
              value: _isReturn,
              onChanged: (v) => setState(() => _isReturn = v),
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: () async {
                final name = _name.text.trim();
                final amt = double.tryParse(_amount.text.trim());
                if (name.isEmpty || amt == null || amt <= 0) {
                  return;
                }
                final ex = widget.existing;
                if (ex == null) {
                  await AppScope.subExpenseRepo.insertLocal(
                    expenseLocalId: widget.expenseLocalId,
                    name: name,
                    amount: amt,
                    isReturn: _isReturn,
                  );
                } else {
                  await AppScope.subExpenseRepo.updateLocal(
                    localId: ex.localId,
                    expenseLocalId: widget.expenseLocalId,
                    name: name,
                    amount: amt,
                    isReturn: _isReturn,
                  );
                }
                if (!context.mounted) {
                  return;
                }
                Navigator.of(context).pop(true);
              },
              child: const Text("Save locally"),
            ),
          ],
        ),
      ),
    );
  }
}
