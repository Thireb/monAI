import "../repositories/expense_repository.dart";
import "../repositories/tag_repository.dart";
import "../repositories/tag_transfer_repository.dart";

/// Per-account totals: expense sums adjusted by transfers (out -, in +).
class AccountBreakdownEntry {
  const AccountBreakdownEntry({
    required this.tagServerId,
    required this.name,
    required this.color,
    required this.amount,
  });

  final int tagServerId;
  final String name;
  final String color;
  final double amount;
}

List<AccountBreakdownEntry> buildAccountBreakdown({
  required List<ExpenseRow> expenses,
  required List<TagTransferRow> transfers,
  required List<TagRow> tags,
}) {
  final byId = <int, TagRow>{
    for (final t in tags)
      if (t.serverId != null) t.serverId!: t,
  };
  final totals = <int, double>{};
  final meta = <int, ({String name, String color})>{};

  void ensure(int tagServerId) {
    if (meta.containsKey(tagServerId)) {
      return;
    }
    final tag = byId[tagServerId];
    meta[tagServerId] = (
      name: tag?.name ?? "Tag #$tagServerId",
      color: tag?.color ?? "#2196f3",
    );
    totals.putIfAbsent(tagServerId, () => 0);
  }

  for (final e in expenses) {
    final tid = e.tagServerId;
    if (tid == null) {
      continue;
    }
    ensure(tid);
    totals[tid] = (totals[tid] ?? 0) + e.amount;
  }
  for (final x in transfers) {
    ensure(x.fromTagServerId);
    ensure(x.toTagServerId);
    totals[x.fromTagServerId] = (totals[x.fromTagServerId] ?? 0) - x.amount;
    totals[x.toTagServerId] = (totals[x.toTagServerId] ?? 0) + x.amount;
  }

  final out = <AccountBreakdownEntry>[];
  for (final entry in totals.entries) {
    if (entry.value == 0) {
      continue;
    }
    final m = meta[entry.key]!;
    out.add(
      AccountBreakdownEntry(
        tagServerId: entry.key,
        name: m.name,
        color: m.color,
        amount: entry.value,
      ),
    );
  }
  out.sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
  return out;
}
