import "package:sqflite/sqflite.dart";

import "../database/app_database.dart";

typedef TagTransferRow = ({
  int localId,
  int? serverId,
  int budgetLocalId,
  int? budgetServerId,
  int fromTagServerId,
  int toTagServerId,
  double amount,
  String dateIso,
  String note,
  String? serverUpdatedAtIso,
  int dirty,
});

class TagTransferRepository {
  TagTransferRepository(this._db);

  final AppDatabase _db;

  static const String _selectCols = """
SELECT t.id AS tid, t.server_id AS tsid, t.budget_local_id AS blid,
       b.server_id AS bsid,
       t.from_tag_server_id AS ftag, t.to_tag_server_id AS ttag,
       t.amount AS tamount, t.date AS tdate, t.note AS tnote,
       t.server_updated_at AS tupd, t.dirty AS tdirty
""";

  Future<List<TagTransferRow>> listForBudgetLocalId(int budgetLocalId) async {
    final db = await _db.database;
    final rows = await db.rawQuery("""
$_selectCols
FROM tag_transfer t
JOIN budget b ON b.id = t.budget_local_id
WHERE t.deleted = 0 AND t.budget_local_id = ?
ORDER BY t.id DESC
""", [budgetLocalId]);
    return rows.map(_fromJoinMap).toList();
  }

  Future<List<TagTransferRow>> dirtyRowsReadyToPush() async {
    final db = await _db.database;
    final rows = await db.rawQuery("""
$_selectCols
FROM tag_transfer t
JOIN budget b ON b.id = t.budget_local_id
WHERE t.deleted = 0 AND t.dirty = 1 AND b.server_id IS NOT NULL AND b.deleted = 0
ORDER BY t.id ASC
""");
    return rows.map(_fromJoinMap).toList();
  }

  Future<List<TagTransferRow>> dirtyDeletedRowsReadyToPush() async {
    final db = await _db.database;
    final rows = await db.rawQuery("""
$_selectCols
FROM tag_transfer t
JOIN budget b ON b.id = t.budget_local_id
WHERE t.deleted = 1 AND t.dirty = 1 AND t.server_id IS NOT NULL
  AND b.server_id IS NOT NULL AND b.deleted = 0
ORDER BY t.id ASC
""");
    return rows.map(_fromJoinMap).toList();
  }

  Future<int> insertLocal({
    required int budgetLocalId,
    required int fromTagServerId,
    required int toTagServerId,
    required double amount,
    required String dateIso,
    String note = "",
  }) async {
    final db = await _db.database;
    return db.insert("tag_transfer", {
      "budget_local_id": budgetLocalId,
      "from_tag_server_id": fromTagServerId,
      "to_tag_server_id": toTagServerId,
      "amount": amount,
      "date": dateIso,
      "note": note,
      "dirty": 1,
      "deleted": 0,
    });
  }

  Future<void> markDeletedLocal(int localId) async {
    final db = await _db.database;
    await db.update(
      "tag_transfer",
      {"deleted": 1, "dirty": 1},
      where: "id = ?",
      whereArgs: [localId],
    );
  }

  Future<void> upsertFromServer({
    required int serverId,
    required int budgetServerId,
    required int fromTagServerId,
    required int toTagServerId,
    required double amount,
    required String dateIso,
    required String note,
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
      "tag_transfer",
      where: "server_id = ?",
      whereArgs: [serverId],
    );
    if (existing.isEmpty) {
      await db.insert("tag_transfer", {
        "server_id": serverId,
        "budget_local_id": budgetLocalId,
        "from_tag_server_id": fromTagServerId,
        "to_tag_server_id": toTagServerId,
        "amount": amount,
        "date": dateIso,
        "note": note,
        "server_updated_at": serverUpdatedAtIso,
        "dirty": 0,
        "deleted": 0,
      });
      return;
    }
    final lid = existing.first["id"] as int;
    await db.update(
      "tag_transfer",
      {
        "budget_local_id": budgetLocalId,
        "from_tag_server_id": fromTagServerId,
        "to_tag_server_id": toTagServerId,
        "amount": amount,
        "date": dateIso,
        "note": note,
        "server_updated_at": serverUpdatedAtIso,
        "dirty": 0,
        "deleted": 0,
      },
      where: "id = ?",
      whereArgs: [lid],
    );
  }

  Future<void> applyPushServerIds(
    List<TagTransferRow> pushed,
    List<dynamic> serverIds,
  ) async {
    if (pushed.length != serverIds.length) {
      return;
    }
    final db = await _db.database;
    for (var i = 0; i < pushed.length; i++) {
      final sid = serverIds[i];
      final int? id = sid is int ? sid : (sid is num ? sid.toInt() : null);
      if (id == null) {
        continue;
      }
      await db.update(
        "tag_transfer",
        {"server_id": id, "dirty": 0},
        where: "id = ?",
        whereArgs: [pushed[i].localId],
      );
    }
  }

  Future<void> purgeLocalsAfterDeletePush(List<int> localIds) async {
    if (localIds.isEmpty) {
      return;
    }
    final db = await _db.database;
    final placeholders = List.filled(localIds.length, "?").join(",");
    await db.delete(
      "tag_transfer",
      where: "id IN ($placeholders)",
      whereArgs: localIds,
    );
  }

  Future<void> removeSyncedRowsNotInServerIdSet(Set<int> serverIds) async {
    final db = await _db.database;
    final rows = await db.query(
      "tag_transfer",
      columns: ["id", "server_id"],
      where: "server_id IS NOT NULL AND dirty = 0 AND deleted = 0",
    );
    for (final row in rows) {
      final sid = row["server_id"] as int?;
      if (sid == null || serverIds.contains(sid)) {
        continue;
      }
      await db.delete("tag_transfer", where: "id = ?", whereArgs: [row["id"]]);
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

  TagTransferRow _fromJoinMap(Map<String, Object?> m) {
    return (
      localId: m["tid"] as int,
      serverId: m["tsid"] as int?,
      budgetLocalId: m["blid"] as int,
      budgetServerId: m["bsid"] as int?,
      fromTagServerId: m["ftag"] as int,
      toTagServerId: m["ttag"] as int,
      amount: (m["tamount"] as num).toDouble(),
      dateIso: (m["tdate"] as String?) ?? "",
      note: (m["tnote"] as String?) ?? "",
      serverUpdatedAtIso: m["tupd"] as String?,
      dirty: m["tdirty"] as int,
    );
  }
}
