import "package:path/path.dart" as p;
import "package:path_provider/path_provider.dart";
import "package:sqflite/sqflite.dart";

const int _dbVersion = 2;

/// Local SQLite for offline budgeting. Server sync will map rows to Django later.
class AppDatabase {
  AppDatabase._();

  static final AppDatabase instance = AppDatabase._();

  /// When set (e.g. in widget tests), DB file is created under this directory instead
  /// of using path_provider (which is unreliable in VM tests).
  static String? testDocumentsOverride;

  Database? _db;

  /// Clears the singleton connection (for tests only).
  Future<void> resetForTesting() async {
    if (_db != null) {
      await _db!.close();
      _db = null;
    }
  }

  Future<void> closeForTesting() async {
    await resetForTesting();
  }

  Future<Database> get database async {
    if (_db != null) {
      return _db!;
    }
    _db = await _open();
    return _db!;
  }

  Future<Database> _open() async {
    final String basePath;
    final override = testDocumentsOverride;
    if (override != null && override.isNotEmpty) {
      basePath = override;
    } else {
      final dir = await getApplicationDocumentsDirectory();
      basePath = dir.path;
    }
    final path = p.join(basePath, "budget_mobile.db");
    return openDatabase(
      path,
      version: _dbVersion,
      onCreate: (db, version) async {
        await _createSchema(db);
      },
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 2) {
          await db.execute(
            "ALTER TABLE budget ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0",
          );
          await db.execute(
            "ALTER TABLE budget ADD COLUMN server_updated_at TEXT",
          );
        }
      },
    );
  }

  Future<void> _createSchema(Database db) async {
    await db.execute("""
CREATE TABLE budget (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  server_id INTEGER,
  month TEXT NOT NULL,
  income REAL NOT NULL DEFAULT 0,
  currency TEXT NOT NULL DEFAULT 'PKR',
  is_archived INTEGER NOT NULL DEFAULT 0,
  updated_at INTEGER NOT NULL,
  server_updated_at TEXT,
  dirty INTEGER NOT NULL DEFAULT 0,
  deleted INTEGER NOT NULL DEFAULT 0
);
""");
    await db.execute("""
CREATE TABLE meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
""");
  }

  Future<int> countBudgets() async {
    final db = await database;
    final rows = await db.rawQuery(
      "SELECT COUNT(*) AS c FROM budget WHERE deleted = 0",
    );
    final raw = rows.first["c"];
    if (raw is int) {
      return raw;
    }
    return int.tryParse(raw.toString()) ?? 0;
  }
}
