import "package:flutter_test/flutter_test.dart";

import "package:budget_mobile/repositories/expense_repository.dart";
import "package:budget_mobile/repositories/tag_repository.dart";
import "package:budget_mobile/repositories/tag_transfer_repository.dart";
import "package:budget_mobile/utils/account_breakdown.dart";

ExpenseRow _exp({
  required int tagServerId,
  required double amount,
}) {
  return (
    localId: 1,
    serverId: 1,
    budgetLocalId: 1,
    budgetServerId: 1,
    name: "E",
    amount: amount,
    isRecurring: false,
    categoryServerId: null,
    tagServerId: tagServerId,
    billReminderServerId: null,
    serverUpdatedAtIso: null,
    dirty: 0,
  );
}

TagRow _tag(int sid, String name) {
  return (
    localId: sid,
    serverId: sid,
    name: name,
    slug: name.toLowerCase(),
    description: "",
    color: "#2196f3",
    isActive: true,
    serverUpdatedAtIso: null,
    dirty: 0,
  );
}

TagTransferRow _xfer({
  required int from,
  required int to,
  required double amount,
}) {
  return (
    localId: 1,
    serverId: 1,
    budgetLocalId: 1,
    budgetServerId: 1,
    fromTagServerId: from,
    toTagServerId: to,
    amount: amount,
    dateIso: "2024-01-01",
    note: "",
    serverUpdatedAtIso: null,
    dirty: 0,
  );
}

void main() {
  test("account breakdown applies transfers", () {
    final rows = buildAccountBreakdown(
      expenses: [_exp(tagServerId: 1, amount: 300)],
      transfers: [_xfer(from: 1, to: 2, amount: 100)],
      tags: [_tag(1, "Cash"), _tag(2, "Bank")],
    );
    final byName = {for (final r in rows) r.name: r.amount};
    expect(byName["Cash"], 200);
    expect(byName["Bank"], 100);
  });
}
