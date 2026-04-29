import "package:sqflite/sqflite.dart";

import "../database/app_database.dart";

typedef TagRow = ({
  int localId,
  int? serverId,
  String name,
  String slug,
  String description,
  String color,
  bool isActive,
  String? serverUpdatedAtIso,
  int dirty,
});

class TagRepository {
  TagRepository(this._db);

  final AppDatabase _db;

  Future<List<TagRow>> listNonDeleted() async {
    final db = await _db.database;
    final rows = await db.query(
      "tag",
      where: "deleted = 0",
      orderBy: "name ASC",
    );
    return rows.map(_fromMap).toList();
  }

  Future<List<TagRow>> dirtyRows() async {
    final db = await _db.database;
    final rows = await db.query(
      "tag",
      where: "dirty = 1 AND deleted = 0",
      orderBy: "id ASC",
    );
    return rows.map(_fromMap).toList();
  }

  Future<void> upsertFromServer({
    required int serverId,
    required String name,
    required String slug,
    required String description,
    required String color,
    required bool isActive,
    required String serverUpdatedAtIso,
  }) async {
    final db = await _db.database;
    final existing = await db.query(
      "tag",
      where: "server_id = ?",
      whereArgs: [serverId],
    );
    if (existing.isEmpty) {
      await db.insert("tag", {
        "server_id": serverId,
        "name": name,
        "slug": slug,
        "description": description,
        "color": color,
        "is_active": isActive ? 1 : 0,
        "server_updated_at": serverUpdatedAtIso,
        "dirty": 0,
        "deleted": 0,
      });
      return;
    }
    final lid = existing.first["id"] as int;
    await db.update(
      "tag",
      {
        "name": name,
        "slug": slug,
        "description": description,
        "color": color,
        "is_active": isActive ? 1 : 0,
        "server_updated_at": serverUpdatedAtIso,
        "dirty": 0,
      },
      where: "id = ?",
      whereArgs: [lid],
    );
  }

  Future<int> insertLocal({
    required String name,
    String description = "",
    String color = "#2196f3",
    bool isActive = true,
  }) async {
    final slug = name.toLowerCase().replaceAll(RegExp(r"[^a-z0-9]+"), "-");
    final db = await _db.database;
    return db.insert("tag", {
      "name": name,
      "slug": slug,
      "description": description,
      "color": color,
      "is_active": isActive ? 1 : 0,
      "server_updated_at": null,
      "dirty": 1,
      "deleted": 0,
    });
  }

  Future<void> updateLocal({
    required int localId,
    required String name,
    String description = "",
    String color = "#2196f3",
    bool isActive = true,
  }) async {
    final slug = name.toLowerCase().replaceAll(RegExp(r"[^a-z0-9]+"), "-");
    final db = await _db.database;
    await db.update(
      "tag",
      {
        "name": name,
        "slug": slug,
        "description": description,
        "color": color,
        "is_active": isActive ? 1 : 0,
        "dirty": 1,
      },
      where: "id = ?",
      whereArgs: [localId],
    );
  }

  Future<void> applyPushServerIds(List<TagRow> pushed, List<dynamic> serverIds) async {
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
        "tag",
        {"server_id": id, "dirty": 0},
        where: "id = ?",
        whereArgs: [pushed[i].localId],
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

  TagRow _fromMap(Map<String, Object?> m) {
    final act = m["is_active"];
    return (
      localId: m["id"] as int,
      serverId: m["server_id"] as int?,
      name: m["name"] as String,
      slug: (m["slug"] as String?) ?? "",
      description: (m["description"] as String?) ?? "",
      color: (m["color"] as String?) ?? "#2196f3",
      isActive: act == 1 || act == true,
      serverUpdatedAtIso: m["server_updated_at"] as String?,
      dirty: m["dirty"] as int,
    );
  }
}
