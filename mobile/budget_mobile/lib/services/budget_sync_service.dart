import "../repositories/budget_repository.dart";
import "../repositories/category_repository.dart";
import "../repositories/expense_repository.dart";
import "../repositories/sub_expense_repository.dart";
import "../repositories/tag_repository.dart";
import "mobile_budget_api_client.dart";

const String _kBudgetCursor = "budget_sync_last_updated_after";
const String _kCategoryCursor = "category_sync_last_updated_after";
const String _kTagCursor = "tag_sync_last_updated_after";
const String _kExpenseCursor = "expense_sync_last_updated_after";
const String _kSubExpenseCursor = "sub_expense_sync_last_updated_after";

/// Push dirty categories → tags → budgets → expenses, then pull each table.
/// Expense and sub-expense pulls always fetch the full server list and prune
/// local synced rows missing from that list so web deletes apply on device.
class BudgetSyncService {
  BudgetSyncService(
    this._api,
    this._budgetRepo,
    this._categoryRepo,
    this._tagRepo,
    this._expenseRepo,
    this._subExpenseRepo,
  );

  final MobileBudgetApiClient _api;
  final BudgetRepository _budgetRepo;
  final CategoryRepository _categoryRepo;
  final TagRepository _tagRepo;
  final ExpenseRepository _expenseRepo;
  final SubExpenseRepository _subExpenseRepo;

  Future<bool> syncAll() async {
    try {
      if (!await _pushCategories()) {
        return false;
      }
      if (!await _pushTags()) {
        return false;
      }
      if (!await _pushBudgets()) {
        return false;
      }
      if (!await _pushExpenses()) {
        return false;
      }
      if (!await _pushSubExpenses()) {
        return false;
      }
      if (!await _pushDeletedSubExpenses()) {
        return false;
      }
      if (!await _pushDeletedExpenses()) {
        return false;
      }
      if (!await _pullCategories()) {
        return false;
      }
      if (!await _pullTags()) {
        return false;
      }
      if (!await _pullBudgets()) {
        return false;
      }
      if (!await _pullExpenses()) {
        return false;
      }
      return _pullSubExpenses();
    } on Object {
      return false;
    }
  }

  /// After a local delete, push tombstones and refresh expense lists from the server.
  Future<bool> syncExpenseDeletes() async {
    try {
      if (!await _pushDeletedSubExpenses()) {
        return false;
      }
      if (!await _pushDeletedExpenses()) {
        return false;
      }
      if (!await _pullExpenses()) {
        return false;
      }
      return _pullSubExpenses();
    } on Object {
      return false;
    }
  }

  Future<bool> _pushCategories() async {
    final dirty = await _categoryRepo.dirtyRows();
    if (dirty.isEmpty) {
      return true;
    }
    final payloads = <Map<String, dynamic>>[];
    for (final r in dirty) {
      final m = <String, dynamic>{
        "name": r.name,
        "description": r.description,
        "icon": r.icon,
        "color": r.color,
      };
      if (r.serverId != null) {
        m["id"] = r.serverId;
      }
      payloads.add(m);
    }
    final response = await _api.pushCategories(payloads);
    if (response == null) {
      return false;
    }
    final ids = response["server_ids"];
    if (ids is! List) {
      return false;
    }
    await _categoryRepo.applyPushServerIds(dirty, ids);
    return true;
  }

  Future<bool> _pushTags() async {
    final dirty = await _tagRepo.dirtyRows();
    if (dirty.isEmpty) {
      return true;
    }
    final payloads = <Map<String, dynamic>>[];
    for (final r in dirty) {
      final m = <String, dynamic>{
        "name": r.name,
        "description": r.description,
        "color": r.color,
        "is_active": r.isActive,
      };
      if (r.serverId != null) {
        m["id"] = r.serverId;
      }
      payloads.add(m);
    }
    final response = await _api.pushTags(payloads);
    if (response == null) {
      return false;
    }
    final ids = response["server_ids"];
    if (ids is! List) {
      return false;
    }
    await _tagRepo.applyPushServerIds(dirty, ids);
    return true;
  }

  Future<bool> _pushBudgets() async {
    final dirty = await _budgetRepo.dirtyRows();
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
    await _budgetRepo.applyPushServerIds(dirty, ids);
    return true;
  }

  Future<bool> _pushExpenses() async {
    final dirty = await _expenseRepo.dirtyRowsReadyToPush();
    final ready = dirty.where((r) => r.budgetServerId != null).toList();
    if (ready.isEmpty) {
      return true;
    }
    final payloads = <Map<String, dynamic>>[];
    for (final r in ready) {
      final m = <String, dynamic>{
        "budget_id": r.budgetServerId!,
        "name": r.name,
        "amount": r.amount.toStringAsFixed(2),
        "is_recurring": r.isRecurring,
        "category_id": r.categoryServerId,
        "tag_id": r.tagServerId,
      };
      if (r.billReminderServerId != null) {
        m["bill_reminder_id"] = r.billReminderServerId;
      }
      if (r.serverId != null) {
        m["id"] = r.serverId;
      }
      payloads.add(m);
    }
    final response = await _api.pushExpenses(payloads);
    if (response == null) {
      return false;
    }
    final ids = response["server_ids"];
    if (ids is! List) {
      return false;
    }
    await _expenseRepo.applyPushServerIds(ready, ids);
    return true;
  }

  Future<bool> _pushDeletedSubExpenses() async {
    final ready = await _subExpenseRepo.dirtyDeletedRowsReadyToPush();
    if (ready.isEmpty) {
      return true;
    }
    final payloads = <Map<String, dynamic>>[];
    for (final r in ready) {
      payloads.add({
        "id": r.serverId,
        "deleted": true,
      });
    }
    final response = await _api.pushSubExpenses(payloads);
    if (response == null) {
      return false;
    }
    final ids = response["server_ids"];
    if (ids is! List || ready.length != ids.length) {
      return false;
    }
    await _subExpenseRepo.purgeLocalsAfterDeletePush(
      ready.map((r) => r.localId).toList(),
    );
    return true;
  }

  Future<bool> _pushDeletedExpenses() async {
    final ready = await _expenseRepo.dirtyDeletedRowsReadyToPush();
    if (ready.isEmpty) {
      return true;
    }
    final payloads = <Map<String, dynamic>>[];
    for (final r in ready) {
      payloads.add({
        "id": r.serverId,
        "deleted": true,
      });
    }
    final response = await _api.pushExpenses(payloads);
    if (response == null) {
      return false;
    }
    final ids = response["server_ids"];
    if (ids is! List || ready.length != ids.length) {
      return false;
    }
    await _expenseRepo.purgeLocalsAfterDeletePush(
      ready.map((r) => r.localId).toList(),
    );
    return true;
  }

  Future<bool> _pushSubExpenses() async {
    final dirty = await _subExpenseRepo.dirtyRowsReadyToPush();
    final ready = dirty.where((r) => r.expenseServerId != null).toList();
    if (ready.isEmpty) {
      return true;
    }
    final payloads = <Map<String, dynamic>>[];
    for (final r in ready) {
      final m = <String, dynamic>{
        "expense_id": r.expenseServerId!,
        "name": r.name,
        "amount": r.amount.toStringAsFixed(2),
        "is_return": r.isReturn,
      };
      if (r.serverId != null) {
        m["id"] = r.serverId;
      }
      payloads.add(m);
    }
    final response = await _api.pushSubExpenses(payloads);
    if (response == null) {
      return false;
    }
    final ids = response["server_ids"];
    if (ids is! List || ready.length != ids.length) {
      return false;
    }
    await _subExpenseRepo.applyPushServerIds(ready, ids);
    return true;
  }

  Future<bool> _pullCategories() async {
    final cursor = await _categoryRepo.getMeta(_kCategoryCursor);
    final data = await _api.pullCategories(cursor);
    if (data == null) {
      return false;
    }
    final list = data["categories"];
    if (list is! List) {
      return false;
    }
    String? maxIso;
    for (final raw in list) {
      if (raw is! Map) {
        continue;
      }
      final item = Map<String, dynamic>.from(raw);
      final sid = _asInt(item["id"]);
      if (sid == null) {
        continue;
      }
      final name = item["name"] as String?;
      if (name == null) {
        continue;
      }
      final slug = (item["slug"] as String?) ?? "";
      final desc = (item["description"] as String?) ?? "";
      final icon = (item["icon"] as String?) ?? "";
      final color = (item["color"] as String?) ?? "#000000";
      final upd = item["updated_at"] as String?;
      if (upd == null || upd.isEmpty) {
        continue;
      }
      await _categoryRepo.upsertFromServer(
        serverId: sid,
        name: name,
        slug: slug,
        description: desc,
        icon: icon,
        color: color,
        serverUpdatedAtIso: upd,
      );
      if (maxIso == null || upd.compareTo(maxIso) > 0) {
        maxIso = upd;
      }
    }
    if (maxIso != null) {
      await _categoryRepo.setMeta(_kCategoryCursor, maxIso);
    }
    return true;
  }

  Future<bool> _pullTags() async {
    final cursor = await _tagRepo.getMeta(_kTagCursor);
    final data = await _api.pullTags(cursor);
    if (data == null) {
      return false;
    }
    final list = data["tags"];
    if (list is! List) {
      return false;
    }
    String? maxIso;
    for (final raw in list) {
      if (raw is! Map) {
        continue;
      }
      final item = Map<String, dynamic>.from(raw);
      final sid = _asInt(item["id"]);
      if (sid == null) {
        continue;
      }
      final name = item["name"] as String?;
      if (name == null) {
        continue;
      }
      final slug = (item["slug"] as String?) ?? "";
      final desc = (item["description"] as String?) ?? "";
      final color = (item["color"] as String?) ?? "#2196f3";
      final active = item["is_active"] == true;
      final upd = item["updated_at"] as String?;
      if (upd == null || upd.isEmpty) {
        continue;
      }
      await _tagRepo.upsertFromServer(
        serverId: sid,
        name: name,
        slug: slug,
        description: desc,
        color: color,
        isActive: active,
        serverUpdatedAtIso: upd,
      );
      if (maxIso == null || upd.compareTo(maxIso) > 0) {
        maxIso = upd;
      }
    }
    if (maxIso != null) {
      await _tagRepo.setMeta(_kTagCursor, maxIso);
    }
    return true;
  }

  Future<bool> _pullBudgets() async {
    final cursor = await _budgetRepo.getMeta(_kBudgetCursor);
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
      final sid = _asInt(item["id"]);
      if (sid == null) {
        continue;
      }
      final month = item["month"] as String?;
      if (month == null) {
        continue;
      }
      final incomeVal = _asDouble(item["income"]);
      if (incomeVal == null) {
        continue;
      }
      final currency = item["currency"] as String?;
      if (currency == null) {
        continue;
      }
      final isArchived = item["is_archived"] == true;
      final updatedIso = item["updated_at"] as String?;
      if (updatedIso == null || updatedIso.isEmpty) {
        continue;
      }
      await _budgetRepo.upsertFromServer(
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
      await _budgetRepo.setMeta(_kBudgetCursor, maxIso);
    }
    return true;
  }

  Future<bool> _pullExpenses() async {
    // Always request the full list: cursor-based incremental pulls never include
    // rows deleted on the server, so the client would keep stale copies forever.
    final data = await _api.pullExpenses(null);
    if (data == null) {
      return false;
    }
    final list = data["expenses"];
    if (list is! List) {
      return false;
    }
    String? maxIso;
    final serverIds = <int>{};
    for (final raw in list) {
      if (raw is! Map) {
        continue;
      }
      final item = Map<String, dynamic>.from(raw);
      final sid = _asInt(item["id"]);
      if (sid == null) {
        continue;
      }
      serverIds.add(sid);
      final budgetSid = _asInt(item["budget_id"]);
      if (budgetSid == null) {
        continue;
      }
      final name = item["name"] as String?;
      if (name == null) {
        continue;
      }
      final amountVal = _asDouble(item["amount"]);
      if (amountVal == null) {
        continue;
      }
      final rec = item["is_recurring"] == true;
      final cat = _asInt(item["category_id"]);
      final tag = _asInt(item["tag_id"]);
      final billRem = _asInt(item["bill_reminder_id"]);
      final updatedIso = item["updated_at"] as String?;
      if (updatedIso == null || updatedIso.isEmpty) {
        continue;
      }
      await _expenseRepo.upsertFromServer(
        serverId: sid,
        budgetServerId: budgetSid,
        name: name,
        amount: amountVal,
        isRecurring: rec,
        categoryId: cat,
        tagId: tag,
        billReminderId: billRem,
        serverUpdatedAtIso: updatedIso,
      );
      if (maxIso == null || updatedIso.compareTo(maxIso) > 0) {
        maxIso = updatedIso;
      }
    }
    await _expenseRepo.removeSyncedRowsNotInServerIdSet(serverIds);
    if (maxIso != null) {
      await _expenseRepo.setMeta(_kExpenseCursor, maxIso);
    }
    return true;
  }

  Future<bool> _pullSubExpenses() async {
    final data = await _api.pullSubExpenses(null);
    if (data == null) {
      return false;
    }
    final list = data["sub_expenses"];
    if (list is! List) {
      return false;
    }
    String? maxIso;
    final serverIds = <int>{};
    for (final raw in list) {
      if (raw is! Map) {
        continue;
      }
      final item = Map<String, dynamic>.from(raw);
      final sid = _asInt(item["id"]);
      if (sid == null) {
        continue;
      }
      serverIds.add(sid);
      final expenseSid = _asInt(item["expense_id"]);
      if (expenseSid == null) {
        continue;
      }
      final name = item["name"] as String?;
      if (name == null) {
        continue;
      }
      final amountVal = _asDouble(item["amount"]);
      if (amountVal == null) {
        continue;
      }
      final isRet = item["is_return"] == true;
      final updatedIso = item["updated_at"] as String?;
      if (updatedIso == null || updatedIso.isEmpty) {
        continue;
      }
      await _subExpenseRepo.upsertFromServer(
        serverId: sid,
        expenseServerId: expenseSid,
        name: name,
        amount: amountVal,
        isReturn: isRet,
        serverUpdatedAtIso: updatedIso,
      );
      if (maxIso == null || updatedIso.compareTo(maxIso) > 0) {
        maxIso = updatedIso;
      }
    }
    await _subExpenseRepo.removeSyncedRowsNotInServerIdSet(serverIds);
    if (maxIso != null) {
      await _subExpenseRepo.setMeta(_kSubExpenseCursor, maxIso);
    }
    return true;
  }

  int? _asInt(dynamic v) {
    if (v is int) {
      return v;
    }
    if (v is num) {
      return v.toInt();
    }
    return null;
  }

  double? _asDouble(dynamic v) {
    if (v is num) {
      return v.toDouble();
    }
    if (v is String) {
      return double.tryParse(v);
    }
    return null;
  }
}
