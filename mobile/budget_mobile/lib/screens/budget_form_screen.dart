import "package:flutter/material.dart";
import "package:flutter/services.dart";

import "../repositories/budget_repository.dart";
import "../theme/minimal_theme.dart";

class BudgetFormScreen extends StatefulWidget {
  const BudgetFormScreen({
    super.key,
    required this.repository,
    this.existing,
  });

  final BudgetRepository repository;
  final BudgetRow? existing;

  @override
  State<BudgetFormScreen> createState() => _BudgetFormScreenState();
}

class _BudgetFormScreenState extends State<BudgetFormScreen> {
  final _monthController = TextEditingController();
  final _incomeController = TextEditingController();
  final _currencyController = TextEditingController();
  bool _archived = false;

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    if (e != null) {
      _monthController.text = e.month.length >= 10 ? e.month.substring(0, 10) : e.month;
      _incomeController.text = e.income.toStringAsFixed(2);
      _currencyController.text = e.currency;
      _archived = e.isArchived;
    } else {
      final now = DateTime.now();
      _monthController.text =
          "${now.year.toString().padLeft(4, "0")}-${now.month.toString().padLeft(2, "0")}-01";
      _incomeController.text = "0";
      _currencyController.text = "PKR";
    }
  }

  @override
  void dispose() {
    _monthController.dispose();
    _incomeController.dispose();
    _currencyController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MinimalPageBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: Text(widget.existing == null ? "New budget" : "Edit budget"),
        ),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextField(
              controller: _monthController,
              decoration: const InputDecoration(
                labelText: "Month (YYYY-MM-DD)",
              ),
              keyboardType: TextInputType.datetime,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _incomeController,
              decoration: const InputDecoration(
                labelText: "Income",
              ),
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              inputFormatters: [
                FilteringTextInputFormatter.allow(RegExp(r"[0-9.]")),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _currencyController,
              decoration: const InputDecoration(
                labelText: "Currency (3 letter)",
              ),
              maxLength: 3,
            ),
            SwitchListTile(
              title: const Text("Archived"),
              value: _archived,
              onChanged: (v) => setState(() => _archived = v),
            ),
            const SizedBox(height: 20),
            FilledButton(
              onPressed: () async {
                final month = _monthController.text.trim();
                final income = double.tryParse(_incomeController.text.trim());
                final cur =
                    _currencyController.text.trim().toUpperCase();
                if (month.isEmpty || income == null || cur.length != 3) {
                  return;
                }
                final e = widget.existing;
                if (e == null) {
                  await widget.repository.insertLocal(
                    month: month,
                    income: income,
                    currency: cur,
                    isArchived: _archived,
                  );
                } else {
                  await widget.repository.updateLocal(
                    localId: e.localId,
                    month: month,
                    income: income,
                    currency: cur,
                    isArchived: _archived,
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
