import "../repositories/budget_repository.dart";
import "mobile_budget_api_client.dart";

const String _pullCursorKey = "budget_sync_last_updated_after";

/// Push dirty local rows then pull server changes (v1: budgets only).
class BudgetSyncService {
  BudgetSyncService(this._api, this._repo);

  final MobileBudgetApiClient _api;
  final BudgetRepository _repo;

  Future<bool> syncBudgets() async {
    try {
      final okPush = await _pushDirty();
      if (!okPush) {
        return false;
      }
      return _pull();
    } on Object {
      return false;
    }
  }

  /// Returns false if there were dirty rows and the server rejected or failed.
  Future<bool> _pushDirty() async {
    final dirty = await _repo.dirtyRows();
    if (dirty.isEmpty) {
      return true;
    }
    final payloads = <Map<String, dynamic>>[];
    for (final r in dirty) {
      final m = <String, dynamic>{
        "month": r.month,
        "income": r.income.toStringAsFixed(2),
        "currency": r.currency,
        "is_archived": r.isArchived,
      };
      if (r.serverId != null) {
        m["id"] = r.serverId;
      }
      payloads.add(m);
    }
    final response = await _api.pushBudgets(payloads);
    if (response == null) {
      return false;
    }
    final ids = response["server_ids"];
    if (ids is! List) {
      return false;
    }
    await _repo.applyPushServerIds(dirty, ids);
    return true;
  }

  Future<bool> _pull() async {
    final cursor = await _repo.getMeta(_pullCursorKey);
    final data = await _api.pullBudgets(cursor);
    if (data == null) {
      return false;
    }
    final list = data["budgets"];
    if (list is! List) {
      return false;
    }
    String? maxIso;
    for (final raw in list) {
      if (raw is! Map) {
        continue;
      }
      final item = Map<String, dynamic>.from(raw);
      final sid = item["id"];
      if (sid is! int) {
        continue;
      }
      final month = item["month"];
      if (month is! String) {
        continue;
      }
      final income = item["income"];
      double? incomeVal;
      if (income is num) {
        incomeVal = income.toDouble();
      } else if (income is String) {
        incomeVal = double.tryParse(income);
      }
      if (incomeVal == null) {
        continue;
      }
      final currency = item["currency"];
      if (currency is! String) {
        continue;
      }
      final archived = item["is_archived"];
      final isArchived = archived == true;
      final updated = item["updated_at"];
      final updatedIso = updated is String ? updated : "";
      if (updatedIso.isEmpty) {
        continue;
      }
      await _repo.upsertFromServer(
        serverId: sid,
        month: month,
        income: incomeVal,
        currency: currency,
        isArchived: isArchived,
        serverUpdatedAtIso: updatedIso,
      );
      if (maxIso == null || updatedIso.compareTo(maxIso) > 0) {
        maxIso = updatedIso;
      }
    }
    if (maxIso != null) {
      await _repo.setMeta(_pullCursorKey, maxIso);
    }
    return true;
  }
}
