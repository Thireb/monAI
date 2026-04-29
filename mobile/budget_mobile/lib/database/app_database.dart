import "package:path/path.dart" as p;
import "package:path_provider/path_provider.dart";
import "package:sqflite/sqflite.dart";

const int _dbVersion = 4;

/// Local SQLite for offline budgeting and server sync.
class AppDatabase {
  AppDatabase._();

  static final AppDatabase instance = AppDatabase._();

  /// When set (e.g. in tests), DB file uses this directory instead of path_provider.
  static String? testDocumentsOverride;

  Database? _db;

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
        if (oldVersion < 3) {
          await _createCatalogTables(db);
        }
        if (oldVersion < 4) {
          await _createSubExpenseTable(db);
        }
      },
    );
  }

  Future<void> _createSubExpenseTable(Database db) async {
    await db.execute("""
CREATE TABLE sub_expense (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  server_id INTEGER,
  expense_local_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  amount REAL NOT NULL,
  is_return INTEGER NOT NULL DEFAULT 0,
  server_updated_at TEXT,
  dirty INTEGER NOT NULL DEFAULT 0,
  deleted INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (expense_local_id) REFERENCES expense (id)
);
""");
  }

  Future<void> _createCatalogTables(Database db) async {
    await db.execute("""
CREATE TABLE category (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  server_id INTEGER,
  name TEXT NOT NULL,
  slug TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  icon TEXT NOT NULL DEFAULT '',
  color TEXT NOT NULL DEFAULT '#000000',
  server_updated_at TEXT,
  dirty INTEGER NOT NULL DEFAULT 0,
  deleted INTEGER NOT NULL DEFAULT 0
);
""");
    await db.execute("""
CREATE TABLE tag (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  server_id INTEGER,
  name TEXT NOT NULL,
  slug TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  color TEXT NOT NULL DEFAULT '#2196f3',
  is_active INTEGER NOT NULL DEFAULT 1,
  server_updated_at TEXT,
  dirty INTEGER NOT NULL DEFAULT 0,
  deleted INTEGER NOT NULL DEFAULT 0
);
""");
    await db.execute("""
CREATE TABLE expense (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  server_id INTEGER,
  budget_local_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  amount REAL NOT NULL,
  is_recurring INTEGER NOT NULL DEFAULT 0,
  category_server_id INTEGER,
  tag_server_id INTEGER,
  server_updated_at TEXT,
  dirty INTEGER NOT NULL DEFAULT 0,
  deleted INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (budget_local_id) REFERENCES budget (id)
);
""");
    await _createSubExpenseTable(db);
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
    await _createCatalogTables(db);
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
