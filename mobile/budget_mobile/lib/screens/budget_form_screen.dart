import "package:flutter/material.dart";
import "package:flutter/services.dart";

import "../repositories/budget_repository.dart";
import "../theme/minimal_theme.dart";
import "../utils/budget_format.dart";

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
  late DateTime _monthFirst;
  final _incomeController = TextEditingController();
  final _currencyController = TextEditingController();
  bool _archived = false;

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    if (e != null) {
      final parsed = parseBudgetMonth(e.month);
      final now = DateTime.now();
      _monthFirst = parsed ?? DateTime(now.year, now.month, 1);
      _incomeController.text = e.income.toStringAsFixed(2);
      _currencyController.text = e.currency;
      _archived = e.isArchived;
    } else {
      final now = DateTime.now();
      _monthFirst = DateTime(now.year, now.month, 1);
      _incomeController.text = "0";
      _currencyController.text = "PKR";
    }
  }

  @override
  void dispose() {
    _incomeController.dispose();
    _currencyController.dispose();
    super.dispose();
  }

  Future<void> _pickMonth() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _monthFirst,
      firstDate: DateTime(2000, 1, 1),
      lastDate: DateTime(2100, 12, 1),
      helpText: "Select budget month",
    );
    if (picked == null || !mounted) {
      return;
    }
    setState(() {
      _monthFirst = DateTime(picked.year, picked.month, 1);
    });
  }

  @override
  Widget build(BuildContext context) {
    final monthLabel = formatBudgetMonthLabel(monthFirstDayIso(_monthFirst));
    final monthStored = monthFirstDayIso(_monthFirst);
    return MinimalPageBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: Text(widget.existing == null ? "New budget" : "Edit budget"),
        ),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              "Budget month",
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    color: MinimalColors.textSecondary,
                  ),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: _pickMonth,
              icon: const Icon(Icons.calendar_month_outlined),
              label: Text(monthLabel),
            ),
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(
                "Stored as $monthStored",
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: MinimalColors.textSecondary,
                    ),
              ),
            ),
            const SizedBox(height: 20),
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
            const SizedBox(height: 16),
            TextField(
              controller: _currencyController,
              decoration: const InputDecoration(
                labelText: "Currency",
                hintText: "PKR",
                counterText: "",
              ),
              textCapitalization: TextCapitalization.characters,
              maxLength: 3,
            ),
            const SizedBox(height: 8),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text("Archived"),
              value: _archived,
              onChanged: (v) => setState(() => _archived = v),
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: () async {
                final income = double.tryParse(_incomeController.text.trim());
                final cur = _currencyController.text.trim().toUpperCase();
                if (income == null || cur.length != 3) {
                  return;
                }
                final month = monthFirstDayIso(_monthFirst);
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
