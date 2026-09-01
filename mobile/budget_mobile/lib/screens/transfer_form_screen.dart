import "package:flutter/material.dart";

import "../app_scope.dart";
import "../repositories/budget_repository.dart";
import "../repositories/tag_repository.dart";
import "../theme/minimal_theme.dart";

/// Create a tag-to-tag transfer for a budget month.
class TransferFormScreen extends StatefulWidget {
  const TransferFormScreen({super.key, required this.budget});

  final BudgetRow budget;

  @override
  State<TransferFormScreen> createState() => _TransferFormScreenState();
}

class _TransferFormScreenState extends State<TransferFormScreen> {
  final _amountCtrl = TextEditingController();
  final _noteCtrl = TextEditingController();
  List<TagRow> _tags = [];
  int? _fromId;
  int? _toId;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final tags = await AppScope.tagRepo.listNonDeleted();
    final withServer = tags.where((t) => t.serverId != null).toList();
    if (!mounted) {
      return;
    }
    setState(() => _tags = withServer);
  }

  @override
  void dispose() {
    _amountCtrl.dispose();
    _noteCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final from = _fromId;
    final to = _toId;
    final amount = double.tryParse(_amountCtrl.text.trim());
    if (from == null || to == null) {
      setState(() => _error = "Select both accounts.");
      return;
    }
    if (from == to) {
      setState(() => _error = "Cannot transfer to the same account.");
      return;
    }
    if (amount == null || amount <= 0) {
      setState(() => _error = "Enter a positive amount.");
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    final now = DateTime.now();
    final dateIso =
        "${now.year.toString().padLeft(4, "0")}-${now.month.toString().padLeft(2, "0")}-${now.day.toString().padLeft(2, "0")}";
    await AppScope.tagTransferRepo.insertLocal(
      budgetLocalId: widget.budget.localId,
      fromTagServerId: from,
      toTagServerId: to,
      amount: amount,
      dateIso: dateIso,
      note: _noteCtrl.text.trim(),
    );
    await AppScope.budgetSync.syncAll();
    if (!mounted) {
      return;
    }
    Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Transfer")),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(
            "Moves allocation between accounts. Does not change remaining budget.",
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: MinimalColors.textSecondary,
                ),
          ),
          const SizedBox(height: 20),
          DropdownButtonFormField<int>(
            value: _fromId,
            decoration: const InputDecoration(labelText: "From account"),
            items: _tags
                .map(
                  (t) => DropdownMenuItem(
                    value: t.serverId,
                    child: Text(t.name),
                  ),
                )
                .toList(),
            onChanged: (v) => setState(() => _fromId = v),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<int>(
            value: _toId,
            decoration: const InputDecoration(labelText: "To account"),
            items: _tags
                .map(
                  (t) => DropdownMenuItem(
                    value: t.serverId,
                    child: Text(t.name),
                  ),
                )
                .toList(),
            onChanged: (v) => setState(() => _toId = v),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _amountCtrl,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: InputDecoration(
              labelText: "Amount (${widget.budget.currency})",
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _noteCtrl,
            decoration: const InputDecoration(labelText: "Note (optional)"),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_tags.isEmpty) ...[
            const SizedBox(height: 12),
            Text(
              "Sync tags from the server (More → Sync) so accounts have IDs.",
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: MinimalColors.textSecondary,
                  ),
            ),
          ],
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _saving || _tags.length < 2 ? null : _save,
            child: _saving
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text("Transfer"),
          ),
        ],
      ),
    );
  }
}
