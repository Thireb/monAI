import "package:sqflite/sqflite.dart";

import "../database/app_database.dart";

typedef SubExpenseRow = ({
  int localId,
  int? serverId,
  int expenseLocalId,
  int? expenseServerId,
  String name,
  double amount,
  bool isReturn,
  String? serverUpdatedAtIso,
  int dirty,
});

class SubExpenseRepository {
  SubExpenseRepository(this._db);

  final AppDatabase _db;

  Future<List<SubExpenseRow>> dirtyRowsReadyToPush() async {
    final db = await _db.database;
    final rows = await db.rawQuery("""
SELECT se.id AS sid, se.server_id AS ssid, se.expense_local_id AS elid,
       e.server_id AS esid, se.name AS sname, se.amount AS samt,
       se.is_return AS sret, se.server_updated_at AS supd, se.dirty AS sdirty
FROM sub_expense se
JOIN expense e ON e.id = se.expense_local_id
JOIN budget b ON b.id = e.budget_local_id
WHERE se.deleted = 0 AND se.dirty = 1
  AND e.server_id IS NOT NULL AND e.deleted = 0
  AND b.server_id IS NOT NULL AND b.deleted = 0
ORDER BY se.id ASC
""");
    return rows.map(_fromJoinMap).toList();
  }

  Future<List<SubExpenseRow>> dirtyDeletedRowsReadyToPush() async {
    final db = await _db.database;
    final rows = await db.rawQuery("""
SELECT se.id AS sid, se.server_id AS ssid, se.expense_local_id AS elid,
       e.server_id AS esid, se.name AS sname, se.amount AS samt,
       se.is_return AS sret, se.server_updated_at AS supd, se.dirty AS sdirty
FROM sub_expense se
JOIN expense e ON e.id = se.expense_local_id
JOIN budget b ON b.id = e.budget_local_id
WHERE se.deleted = 1 AND se.dirty = 1 AND se.server_id IS NOT NULL
  AND e.server_id IS NOT NULL AND e.deleted = 0
  AND b.server_id IS NOT NULL AND b.deleted = 0
ORDER BY se.id ASC
""");
    return rows.map(_fromJoinMap).toList();
  }

  /// All sub-expenses for a budget, ordered by parent expense then sub-expense id.
  Future<List<SubExpenseRow>> listForBudgetLocalId(int budgetLocalId) async {
    final db = await _db.database;
    final rows = await db.rawQuery("""
SELECT se.id AS sid, se.server_id AS ssid, se.expense_local_id AS elid,
       e.server_id AS esid, se.name AS sname, se.amount AS samt,
       se.is_return AS sret, se.server_updated_at AS supd, se.dirty AS sdirty
FROM sub_expense se
JOIN expense e ON e.id = se.expense_local_id
WHERE se.deleted = 0 AND e.deleted = 0 AND e.budget_local_id = ?
ORDER BY e.id ASC, se.id ASC
""", [budgetLocalId]);
    return rows.map(_fromJoinMap).toList();
  }

  Future<List<SubExpenseRow>> listForExpenseLocalId(int expenseLocalId) async {
    final db = await _db.database;
    final rows = await db.rawQuery("""
SELECT se.id AS sid, se.server_id AS ssid, se.expense_local_id AS elid,
       e.server_id AS esid, se.name AS sname, se.amount AS samt,
       se.is_return AS sret, se.server_updated_at AS supd, se.dirty AS sdirty
FROM sub_expense se
JOIN expense e ON e.id = se.expense_local_id
WHERE se.deleted = 0 AND se.expense_local_id = ?
ORDER BY se.id ASC
""", [expenseLocalId]);
    return rows.map(_fromJoinMap).toList();
  }

  Future<void> upsertFromServer({
    required int serverId,
    required int expenseServerId,
    required String name,
    required double amount,
    required bool isReturn,
    required String serverUpdatedAtIso,
  }) async {
    final db = await _db.database;
    final expRows = await db.query(
      "expense",
      where: "server_id = ?",
      whereArgs: [expenseServerId],
    );
    if (expRows.isEmpty) {
      return;
    }
    final expenseLocalId = expRows.first["id"] as int;
    final existing = await db.query(
      "sub_expense",
      where: "server_id = ?",
      whereArgs: [serverId],
    );
    if (existing.isEmpty) {
      await db.insert("sub_expense", {
        "server_id": serverId,
        "expense_local_id": expenseLocalId,
        "name": name,
        "amount": amount,
        "is_return": isReturn ? 1 : 0,
        "server_updated_at": serverUpdatedAtIso,
        "dirty": 0,
        "deleted": 0,
      });
      return;
    }
    final lid = existing.first["id"] as int;
    await db.update(
      "sub_expense",
      {
        "expense_local_id": expenseLocalId,
        "name": name,
        "amount": amount,
        "is_return": isReturn ? 1 : 0,
        "server_updated_at": serverUpdatedAtIso,
        "dirty": 0,
      },
      where: "id = ?",
      whereArgs: [lid],
    );
  }

  Future<int> insertLocal({
    required int expenseLocalId,
    required String name,
    required double amount,
    bool isReturn = false,
  }) async {
    final db = await _db.database;
    return db.insert("sub_expense", {
      "expense_local_id": expenseLocalId,
      "name": name,
      "amount": amount,
      "is_return": isReturn ? 1 : 0,
      "server_updated_at": null,
      "dirty": 1,
      "deleted": 0,
    });
  }

  Future<void> updateLocal({
    required int localId,
    required int expenseLocalId,
    required String name,
    required double amount,
    bool isReturn = false,
  }) async {
    final db = await _db.database;
    await db.update(
      "sub_expense",
      {
        "expense_local_id": expenseLocalId,
        "name": name,
        "amount": amount,
        "is_return": isReturn ? 1 : 0,
        "dirty": 1,
      },
      where: "id = ?",
      whereArgs: [localId],
    );
  }

  Future<void> markDeletedLocal(int localId) async {
    final db = await _db.database;
    final rows = await db.query("sub_expense", where: "id = ?", whereArgs: [localId]);
    if (rows.isEmpty) {
      return;
    }
    final serverId = rows.first["server_id"] as int?;
    if (serverId != null) {
      await db.update(
        "sub_expense",
        {"deleted": 1, "dirty": 1},
        where: "id = ?",
        whereArgs: [localId],
      );
    } else {
      await db.delete("sub_expense", where: "id = ?", whereArgs: [localId]);
    }
  }

  Future<void> purgeLocalsAfterDeletePush(List<int> localIds) async {
    if (localIds.isEmpty) {
      return;
    }
    final db = await _db.database;
    await db.transaction((txn) async {
      for (final id in localIds) {
        await txn.delete("sub_expense", where: "id = ?", whereArgs: [id]);
      }
    });
  }

  /// Removes synced local rows whose server_id is absent from [serverIdsPresent].
  /// Skips dirty rows. Orphans whose parent expense row was pruned should already
  /// be gone if [ExpenseRepository.removeSyncedRowsNotInServerIdSet] ran first.
  Future<void> removeSyncedRowsNotInServerIdSet(Set<int> serverIdsPresent) async {
    final db = await _db.database;
    if (serverIdsPresent.isEmpty) {
      await db.delete(
        "sub_expense",
        where: "server_id IS NOT NULL AND deleted = 0 AND dirty = 0",
      );
      return;
    }
    final placeholders = List.filled(serverIdsPresent.length, "?").join(",");
    final args = serverIdsPresent.toList();
    await db.rawDelete(
      """
DELETE FROM sub_expense
WHERE server_id IS NOT NULL AND deleted = 0 AND dirty = 0
  AND server_id NOT IN ($placeholders)
""",
      args,
    );
  }

  Future<void> applyPushServerIds(
    List<SubExpenseRow> pushedInOrder,
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
        "sub_expense",
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

  SubExpenseRow _fromJoinMap(Map<String, Object?> m) {
    final ret = m["sret"];
    return (
      localId: m["sid"] as int,
      serverId: m["ssid"] as int?,
      expenseLocalId: m["elid"] as int,
      expenseServerId: m["esid"] as int?,
      name: m["sname"] as String,
      amount: (m["samt"] as num).toDouble(),
      isReturn: ret == 1 || ret == true,
      serverUpdatedAtIso: m["supd"] as String?,
      dirty: m["sdirty"] as int,
    );
  }
}
