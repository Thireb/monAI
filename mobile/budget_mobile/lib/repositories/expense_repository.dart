import "package:sqflite/sqflite.dart";

import "../database/app_database.dart";

typedef ExpenseRow = ({
  int localId,
  int? serverId,
  int budgetLocalId,
  int? budgetServerId,
  String name,
  double amount,
  bool isRecurring,
  int? categoryServerId,
  int? tagServerId,
  String? serverUpdatedAtIso,
  int dirty,
});

class ExpenseRepository {
  ExpenseRepository(this._db);

  final AppDatabase _db;

  /// Dirty expenses whose budget row has server_id (can push).
  Future<List<ExpenseRow>> dirtyRowsReadyToPush() async {
    final db = await _db.database;
    final rows = await db.rawQuery("""
SELECT e.id AS eid, e.server_id AS esid, e.budget_local_id AS blid, b.server_id AS bsid,
       e.name AS ename, e.amount AS eamount, e.is_recurring AS erec,
       e.category_server_id AS ccat, e.tag_server_id AS etag,
       e.server_updated_at AS eupd, e.dirty AS edirty
FROM expense e
JOIN budget b ON b.id = e.budget_local_id
WHERE e.deleted = 0 AND e.dirty = 1 AND b.server_id IS NOT NULL AND b.deleted = 0
ORDER BY e.id ASC
""");
    return rows.map(_fromJoinMap).toList();
  }

  Future<List<ExpenseRow>> listForBudgetLocalId(int budgetLocalId) async {
    final db = await _db.database;
    final rows = await db.rawQuery("""
SELECT e.id AS eid, e.server_id AS esid, e.budget_local_id AS blid, b.server_id AS bsid,
       e.name AS ename, e.amount AS eamount, e.is_recurring AS erec,
       e.category_server_id AS ccat, e.tag_server_id AS etag,
       e.server_updated_at AS eupd, e.dirty AS edirty
FROM expense e
JOIN budget b ON b.id = e.budget_local_id
WHERE e.deleted = 0 AND e.budget_local_id = ?
ORDER BY e.id ASC
""", [budgetLocalId]);
    return rows.map(_fromJoinMap).toList();
  }

  Future<void> upsertFromServer({
    required int serverId,
    required int budgetServerId,
    required String name,
    required double amount,
    required bool isRecurring,
    int? categoryId,
    int? tagId,
    required String serverUpdatedAtIso,
  }) async {
    final db = await _db.database;
    final budgets = await db.query(
      "budget",
      where: "server_id = ?",
      whereArgs: [budgetServerId],
    );
    if (budgets.isEmpty) {
      return;
    }
    final budgetLocalId = budgets.first["id"] as int;
    final existing = await db.query(
      "expense",
      where: "server_id = ?",
      whereArgs: [serverId],
    );
    if (existing.isEmpty) {
      await db.insert("expense", {
        "server_id": serverId,
        "budget_local_id": budgetLocalId,
        "name": name,
        "amount": amount,
        "is_recurring": isRecurring ? 1 : 0,
        "category_server_id": categoryId,
        "tag_server_id": tagId,
        "server_updated_at": serverUpdatedAtIso,
        "dirty": 0,
        "deleted": 0,
      });
      return;
    }
    final lid = existing.first["id"] as int;
    await db.update(
      "expense",
      {
        "budget_local_id": budgetLocalId,
        "name": name,
        "amount": amount,
        "is_recurring": isRecurring ? 1 : 0,
        "category_server_id": categoryId,
        "tag_server_id": tagId,
        "server_updated_at": serverUpdatedAtIso,
        "dirty": 0,
      },
      where: "id = ?",
      whereArgs: [lid],
    );
  }

  Future<int> insertLocal({
    required int budgetLocalId,
    required String name,
    required double amount,
    bool isRecurring = false,
    int? categoryServerId,
    int? tagServerId,
  }) async {
    final db = await _db.database;
    return db.insert("expense", {
      "budget_local_id": budgetLocalId,
      "name": name,
      "amount": amount,
      "is_recurring": isRecurring ? 1 : 0,
      "category_server_id": categoryServerId,
      "tag_server_id": tagServerId,
      "server_updated_at": null,
      "dirty": 1,
      "deleted": 0,
    });
  }

  Future<void> updateLocal({
    required int localId,
    required int budgetLocalId,
    required String name,
    required double amount,
    bool isRecurring = false,
    int? categoryServerId,
    int? tagServerId,
  }) async {
    final db = await _db.database;
    await db.update(
      "expense",
      {
        "budget_local_id": budgetLocalId,
        "name": name,
        "amount": amount,
        "is_recurring": isRecurring ? 1 : 0,
        "category_server_id": categoryServerId,
        "tag_server_id": tagServerId,
        "dirty": 1,
      },
      where: "id = ?",
      whereArgs: [localId],
    );
  }

  Future<void> applyPushServerIds(
    List<ExpenseRow> pushedInOrder,
    List<dynamic> serverIds,
  ) async {
    if (pushedInOrder.length != serverIds.length) {
      return;
    }
    final db = await _db.database;
    for (var i = 0; i < pushedInOrder.length; i++) {
      final sid = serverIds[i];
      final int? id = sid is int ? sid : (sid is num ? sid.toInt() : null);
      if (id == null) {
        continue;
      }
      await db.update(
        "expense",
        {"server_id": id, "dirty": 0},
        where: "id = ?",
        whereArgs: [pushedInOrder[i].localId],
      );
    }
  }

  Future<String?> getMeta(String key) async {
    final db = await _db.database;
    final rows = await db.query("meta", where: "key = ?", whereArgs: [key]);
    if (rows.isEmpty) {
      return null;
    }
    return rows.first["value"] as String?;
  }

  Future<void> setMeta(String key, String? value) async {
    final db = await _db.database;
    if (value == null || value.isEmpty) {
      await db.delete("meta", where: "key = ?", whereArgs: [key]);
      return;
    }
    await db.insert(
      "meta",
      {"key": key, "value": value},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  ExpenseRow _fromJoinMap(Map<String, Object?> m) {
    final rec = m["erec"];
    return (
      localId: m["eid"] as int,
      serverId: m["esid"] as int?,
      budgetLocalId: m["blid"] as int,
      budgetServerId: m["bsid"] as int?,
      name: m["ename"] as String,
      amount: (m["eamount"] as num).toDouble(),
      isRecurring: rec == 1 || rec == true,
      categoryServerId: m["ccat"] as int?,
      tagServerId: m["etag"] as int?,
      serverUpdatedAtIso: m["eupd"] as String?,
      dirty: m["edirty"] as int,
    );
  }
}
