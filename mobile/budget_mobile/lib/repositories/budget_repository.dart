import "package:sqflite/sqflite.dart";

import "../database/app_database.dart";

typedef BudgetRow = ({
  int localId,
  int? serverId,
  String month,
  double income,
  String currency,
  bool isArchived,
  int updatedAtMs,
  String? serverUpdatedAtIso,
  int dirty,
});

class BudgetRepository {
  BudgetRepository(this._db);

  final AppDatabase _db;

  Future<List<BudgetRow>> listNonDeleted() async {
    final db = await _db.database;
    final rows = await db.query(
      "budget",
      where: "deleted = 0",
      orderBy: "month DESC",
    );
    return rows.map(_rowFromMap).toList();
  }

  Future<int> countNonDeleted() async {
    final db = await _db.database;
    final raw = await db.rawQuery(
      "SELECT COUNT(*) AS c FROM budget WHERE deleted = 0",
    );
    final v = raw.first["c"];
    if (v is int) {
      return v;
    }
    return int.tryParse(v.toString()) ?? 0;
  }

  Future<List<BudgetRow>> dirtyRows() async {
    final db = await _db.database;
    final rows = await db.query(
      "budget",
      where: "dirty = 1 AND deleted = 0",
      orderBy: "id ASC",
    );
    return rows.map(_rowFromMap).toList();
  }

  Future<void> upsertFromServer({
    required int serverId,
    required String month,
    required double income,
    required String currency,
    required bool isArchived,
    required String serverUpdatedAtIso,
  }) async {
    final db = await _db.database;
    final existing = await db.query(
      "budget",
      where: "server_id = ?",
      whereArgs: [serverId],
    );
    final nowMs = DateTime.now().millisecondsSinceEpoch;
    if (existing.isEmpty) {
      await db.insert("budget", {
        "server_id": serverId,
        "month": month,
        "income": income,
        "currency": currency,
        "is_archived": isArchived ? 1 : 0,
        "updated_at": nowMs,
        "server_updated_at": serverUpdatedAtIso,
        "dirty": 0,
        "deleted": 0,
      });
      return;
    }
    final localId = existing.first["id"] as int;
    await db.update(
      "budget",
      {
        "month": month,
        "income": income,
        "currency": currency,
        "is_archived": isArchived ? 1 : 0,
        "updated_at": nowMs,
        "server_updated_at": serverUpdatedAtIso,
        "dirty": 0,
      },
      where: "id = ?",
      whereArgs: [localId],
    );
  }

  /// Offline create: no server_id until push succeeds.
  Future<int> insertLocal({
    required String month,
    required double income,
    String currency = "PKR",
    bool isArchived = false,
  }) async {
    final db = await _db.database;
    final nowMs = DateTime.now().millisecondsSinceEpoch;
    return db.insert("budget", {
      "month": month,
      "income": income,
      "currency": currency,
      "is_archived": isArchived ? 1 : 0,
      "updated_at": nowMs,
      "server_updated_at": null,
      "dirty": 1,
      "deleted": 0,
    });
  }

  Future<void> applyPushServerIds(List<BudgetRow> pushedInOrder, List<dynamic> serverIds) async {
    if (pushedInOrder.length != serverIds.length) {
      return;
    }
    final db = await _db.database;
    final nowMs = DateTime.now().millisecondsSinceEpoch;
    for (var i = 0; i < pushedInOrder.length; i++) {
      final sid = serverIds[i];
      final int? id = sid is int ? sid : (sid is num ? sid.toInt() : null);
      if (id == null) {
        continue;
      }
      await db.update(
        "budget",
        {
          "server_id": id,
          "dirty": 0,
          "updated_at": nowMs,
        },
        where: "id = ?",
        whereArgs: [pushedInOrder[i].localId],
      );
    }
  }

  Future<void> updateLocal({
    required int localId,
    required String month,
    required double income,
    required String currency,
    required bool isArchived,
  }) async {
    final db = await _db.database;
    final nowMs = DateTime.now().millisecondsSinceEpoch;
    await db.update(
      "budget",
      {
        "month": month,
        "income": income,
        "currency": currency,
        "is_archived": isArchived ? 1 : 0,
        "updated_at": nowMs,
        "dirty": 1,
      },
      where: "id = ?",
      whereArgs: [localId],
    );
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
    await db.insert("meta", {"key": key, "value": value},
        conflictAlgorithm: ConflictAlgorithm.replace);
  }

  BudgetRow _rowFromMap(Map<String, Object?> m) {
    final archived = m["is_archived"];
    return (
      localId: m["id"] as int,
      serverId: m["server_id"] as int?,
      month: m["month"] as String,
      income: (m["income"] as num).toDouble(),
      currency: m["currency"] as String,
      isArchived: archived == 1 || archived == true,
      updatedAtMs: m["updated_at"] as int,
      serverUpdatedAtIso: m["server_updated_at"] as String?,
      dirty: m["dirty"] as int,
    );
  }
}
