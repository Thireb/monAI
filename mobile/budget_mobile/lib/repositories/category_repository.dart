import "package:sqflite/sqflite.dart";

import "../database/app_database.dart";

typedef CategoryRow = ({
  int localId,
  int? serverId,
  String name,
  String slug,
  String description,
  String icon,
  String color,
  String? serverUpdatedAtIso,
  int dirty,
});

class CategoryRepository {
  CategoryRepository(this._db);

  final AppDatabase _db;

  Future<List<CategoryRow>> listNonDeleted() async {
    final db = await _db.database;
    final rows = await db.query(
      "category",
      where: "deleted = 0",
      orderBy: "name ASC",
    );
    return rows.map(_fromMap).toList();
  }

  Future<List<CategoryRow>> dirtyRows() async {
    final db = await _db.database;
    final rows = await db.query(
      "category",
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
    required String icon,
    required String color,
    required String serverUpdatedAtIso,
  }) async {
    final db = await _db.database;
    final existing = await db.query(
      "category",
      where: "server_id = ?",
      whereArgs: [serverId],
    );
    if (existing.isEmpty) {
      await db.insert("category", {
        "server_id": serverId,
        "name": name,
        "slug": slug,
        "description": description,
        "icon": icon,
        "color": color,
        "server_updated_at": serverUpdatedAtIso,
        "dirty": 0,
        "deleted": 0,
      });
      return;
    }
    final lid = existing.first["id"] as int;
    await db.update(
      "category",
      {
        "name": name,
        "slug": slug,
        "description": description,
        "icon": icon,
        "color": color,
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
    String icon = "",
    String color = "#000000",
  }) async {
    final slug = name.toLowerCase().replaceAll(RegExp(r"[^a-z0-9]+"), "-");
    final db = await _db.database;
    return db.insert("category", {
      "name": name,
      "slug": slug,
      "description": description,
      "icon": icon,
      "color": color,
      "server_updated_at": null,
      "dirty": 1,
      "deleted": 0,
    });
  }

  Future<void> updateLocal({
    required int localId,
    required String name,
    String description = "",
    String icon = "",
    String color = "#000000",
  }) async {
    final slug = name.toLowerCase().replaceAll(RegExp(r"[^a-z0-9]+"), "-");
    final db = await _db.database;
    await db.update(
      "category",
      {
        "name": name,
        "slug": slug,
        "description": description,
        "icon": icon,
        "color": color,
        "dirty": 1,
      },
      where: "id = ?",
      whereArgs: [localId],
    );
  }

  Future<void> applyPushServerIds(
    List<CategoryRow> pushedInOrder,
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
        "category",
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

  CategoryRow _fromMap(Map<String, Object?> m) {
    return (
      localId: m["id"] as int,
      serverId: m["server_id"] as int?,
      name: m["name"] as String,
      slug: (m["slug"] as String?) ?? "",
      description: (m["description"] as String?) ?? "",
      icon: (m["icon"] as String?) ?? "",
      color: (m["color"] as String?) ?? "#000000",
      serverUpdatedAtIso: m["server_updated_at"] as String?,
      dirty: m["dirty"] as int,
    );
  }
}
