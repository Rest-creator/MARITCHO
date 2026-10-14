import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

/// The app's single SQLite database: the outbound offline queue
/// (`offline_queue`, see `SqliteOutbox`) and the read-side response cache
/// (`cached_responses`).
class DatabaseHelper {
  static final DatabaseHelper _instance = DatabaseHelper._internal();
  factory DatabaseHelper() => _instance;
  DatabaseHelper._internal();

  static Database? _database;

  /// v3: the queue gained per-item retry scheduling (`job_id`,
  /// `next_attempt_at`, `last_error`); the never-used `check_ins` and
  /// `photo_uploads` tables were dropped.
  static const int schemaVersion = 3;

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    final String path = join(await getDatabasesPath(), 'maricho_offline.db');
    return openDatabase(
      path,
      version: schemaVersion,
      onCreate: createSchema,
      onUpgrade: upgradeSchema,
    );
  }

  static Future<void> createSchema(Database db, int version) async {
    await db.execute('''
      CREATE TABLE offline_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        job_id TEXT,
        payload TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        created_at TEXT NOT NULL,
        retry_count INTEGER NOT NULL DEFAULT 0,
        next_attempt_at TEXT,
        last_error TEXT
      )
    ''');
    await _createCachedResponsesTable(db);
  }

  static Future<void> upgradeSchema(
    Database db,
    int oldVersion,
    int newVersion,
  ) async {
    if (oldVersion < 2) {
      await _createCachedResponsesTable(db);
    }
    if (oldVersion < 3) {
      await db.execute('ALTER TABLE offline_queue ADD COLUMN job_id TEXT');
      await db.execute(
        'ALTER TABLE offline_queue ADD COLUMN next_attempt_at TEXT',
      );
      await db.execute('ALTER TABLE offline_queue ADD COLUMN last_error TEXT');
      // The old check-in/photo prototype posted to endpoints the backend
      // never had; anything it queued can never be delivered.
      await db.delete(
        'offline_queue',
        where: 'action_type IN (?, ?)',
        whereArgs: <Object>['SYNC_CHECK_IN', 'SYNC_PHOTO_UPLOAD'],
      );
      await db.execute('DROP TABLE IF EXISTS check_ins');
      await db.execute('DROP TABLE IF EXISTS photo_uploads');
    }
  }

  static Future<void> _createCachedResponsesTable(Database db) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS cached_responses (
        cache_key TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        cached_at TEXT NOT NULL
      )
    ''');
  }

  /// Read-side offline cache: the last successful response for [cacheKey],
  /// used as a fallback when a repository's live fetch fails (see
  /// JobsRepository/WorkersRepository's cache-aside reads). Not the
  /// write-side outbound queue — that's `offline_queue`.
  Future<void> cacheResponse(String cacheKey, String payload) async {
    final Database db = await database;
    await db.insert('cached_responses', <String, Object?>{
      'cache_key': cacheKey,
      'payload': payload,
      'cached_at': DateTime.now().toIso8601String(),
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<String?> getCachedResponse(String cacheKey) async {
    final Database db = await database;
    final List<Map<String, Object?>> rows = await db.query(
      'cached_responses',
      where: 'cache_key = ?',
      whereArgs: <Object>[cacheKey],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return rows.first['payload'] as String;
  }
}
