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
  int? billReminderServerId,
  String? serverUpdatedAtIso,
  int dirty,
});

class ExpenseRepository {
  ExpenseRepository(this._db);

  final AppDatabase _db;

  static const String _selectCols = """
SELECT e.id AS eid, e.server_id AS esid, e.budget_local_id AS blid, b.server_id AS bsid,
       e.name AS ename, e.amount AS eamount, e.is_recurring AS erec,
       e.category_server_id AS ccat, e.tag_server_id AS etag,
       e.bill_reminder_server_id AS brrem,
       e.server_updated_at AS eupd, e.dirty AS edirty
""";

  /// Dirty expenses whose budget row has server_id (can push).
  Future<List<ExpenseRow>> dirtyRowsReadyToPush() async {
    final db = await _db.database;
    final rows = await db.rawQuery("""
$_selectCols
FROM expense e
JOIN budget b ON b.id = e.budget_local_id
WHERE e.deleted = 0 AND e.dirty = 1 AND b.server_id IS NOT NULL AND b.deleted = 0
ORDER BY e.id ASC
""");
    return rows.map(_fromJoinMap).toList();
  }

  /// Soft-deleted expenses that still exist on the server and need a delete push.
  Future<List<ExpenseRow>> dirtyDeletedRowsReadyToPush() async {
    final db = await _db.database;
    final rows = await db.rawQuery("""
$_selectCols
FROM expense e
JOIN budget b ON b.id = e.budget_local_id
WHERE e.deleted = 1 AND e.dirty = 1 AND e.server_id IS NOT NULL
  AND b.server_id IS NOT NULL AND b.deleted = 0
ORDER BY e.id ASC
""");
    return rows.map(_fromJoinMap).toList();
  }

  Future<List<ExpenseRow>> listForBudgetLocalId(int budgetLocalId) async {
    final db = await _db.database;
    final rows = await db.rawQuery("""
$_selectCols
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
    int? billReminderId,
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
        "bill_reminder_server_id": billReminderId,
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
        "bill_reminder_server_id": billReminderId,
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
    int? billReminderServerId,
  }) async {
    final db = await _db.database;
    return db.insert("expense", {
      "budget_local_id": budgetLocalId,
      "name": name,
      "amount": amount,
      "is_recurring": isRecurring ? 1 : 0,
      "category_server_id": categoryServerId,
      "tag_server_id": tagServerId,
      "bill_reminder_server_id": billReminderServerId,
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
    int? billReminderServerId,
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
        "bill_reminder_server_id": billReminderServerId,
        "dirty": 1,
      },
      where: "id = ?",
      whereArgs: [localId],
    );
  }

  /// Marks an expense deleted locally. Unsynced rows are removed; synced rows are
  /// tombstoned for the next push (child sub-expenses are cleared so the server
  /// CASCADE from expense delete does not orphan push entries).
  Future<void> markDeletedLocal(int localId) async {
    final db = await _db.database;
    final rows = await db.query("expense", where: "id = ?", whereArgs: [localId]);
    if (rows.isEmpty) {
      return;
    }
    final serverId = rows.first["server_id"] as int?;
    await db.transaction((txn) async {
      if (serverId != null) {
        await txn.delete(
          "sub_expense",
          where: "expense_local_id = ?",
          whereArgs: [localId],
        );
        await txn.update(
          "expense",
          {"deleted": 1, "dirty": 1},
          where: "id = ?",
          whereArgs: [localId],
        );
      } else {
        await txn.delete(
          "sub_expense",
          where: "expense_local_id = ?",
          whereArgs: [localId],
        );
        await txn.delete("expense", where: "id = ?", whereArgs: [localId]);
      }
    });
  }

  /// After a successful delete push, remove tombstoned rows from the local DB.
  Future<void> purgeLocalsAfterDeletePush(List<int> localIds) async {
    if (localIds.isEmpty) {
      return;
    }
    final db = await _db.database;
    await db.transaction((txn) async {
      for (final id in localIds) {
        await txn.delete("expense", where: "id = ?", whereArgs: [id]);
      }
    });
  }

  /// Removes synced local rows whose server_id is absent from [serverIdsPresent].
  /// Skips dirty rows so offline edits are not wiped. Used after a full pull so
  /// server-side deletes (e.g. web UI) disappear on the device.
  Future<void> removeSyncedRowsNotInServerIdSet(Set<int> serverIdsPresent) async {
    if (serverIdsPresent.isEmpty) {
      final db = await _db.database;
      await db.transaction((txn) async {
        final rows = await txn.query(
          "expense",
          columns: ["id"],
          where: "server_id IS NOT NULL AND deleted = 0 AND dirty = 0",
        );
        for (final r in rows) {
          final lid = r["id"] as int;
          await txn.delete(
            "sub_expense",
            where: "expense_local_id = ?",
            whereArgs: [lid],
          );
          await txn.delete("expense", where: "id = ?", whereArgs: [lid]);
        }
      });
      return;
    }
    final db = await _db.database;
    final placeholders = List.filled(serverIdsPresent.length, "?").join(",");
    final args = serverIdsPresent.toList();
    await db.transaction((txn) async {
      final rows = await txn.rawQuery(
        """
SELECT id FROM expense
WHERE server_id IS NOT NULL AND deleted = 0 AND dirty = 0
  AND server_id NOT IN ($placeholders)
""",
        args,
      );
      for (final r in rows) {
        final lid = r["id"] as int;
        await txn.delete(
          "sub_expense",
          where: "expense_local_id = ?",
          whereArgs: [lid],
        );
        await txn.delete("expense", where: "id = ?", whereArgs: [lid]);
      }
    });
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
      billReminderServerId: m["brrem"] as int?,
      serverUpdatedAtIso: m["eupd"] as String?,
      dirty: m["edirty"] as int,
    );
  }
}
