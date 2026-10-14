import 'dart:convert';

import 'package:sqflite/sqflite.dart';

import 'package:mobile/core/storage/database_helper.dart';
import 'package:mobile/core/sync/outbox.dart';
import 'package:mobile/core/sync/outbox_item.dart';

/// [Outbox] on the `offline_queue` table, so queued work survives the app
/// being closed or the phone restarting.
class SqliteOutbox implements Outbox {
  final DatabaseHelper _dbHelper;

  SqliteOutbox(this._dbHelper);

  static const String _table = 'offline_queue';

  @override
  Future<int> enqueue({
    required String type,
    required String? jobId,
    required Map<String, Object?> payload,
  }) async {
    final Database db = await _dbHelper.database;
    return db.insert(_table, <String, Object?>{
      'action_type': type,
      'job_id': jobId,
      'payload': jsonEncode(payload),
      'status': 'PENDING',
      'created_at': DateTime.now().toUtc().toIso8601String(),
      'retry_count': 0,
    });
  }

  @override
  Future<List<OutboxItem>> due(DateTime now) async {
    final Database db = await _dbHelper.database;
    final List<Map<String, Object?>> rows = await db.query(
      _table,
      where: "status = 'PENDING' AND (next_attempt_at IS NULL OR next_attempt_at <= ?)",
      whereArgs: <Object>[now.toUtc().toIso8601String()],
      orderBy: 'id ASC',
    );
    return rows.map(_fromRow).toList();
  }

  @override
  Future<List<OutboxItem>> undeliveredForJob(String jobId) async {
    final Database db = await _dbHelper.database;
    final List<Map<String, Object?>> rows = await db.query(
      _table,
      where: "job_id = ? AND status IN ('PENDING', 'FAILED')",
      whereArgs: <Object>[jobId],
      orderBy: 'id ASC',
    );
    return rows.map(_fromRow).toList();
  }

  @override
  Future<void> markSent(int id) =>
      _update(id, <String, Object?>{'status': 'COMPLETED', 'last_error': null});

  @override
  Future<void> reschedule(
    int id, {
    required int attempts,
    required DateTime nextAttemptAt,
    required String? error,
    Map<String, Object?>? payload,
  }) => _update(id, <String, Object?>{
    'retry_count': attempts,
    'next_attempt_at': nextAttemptAt.toUtc().toIso8601String(),
    'last_error': error,
    if (payload != null) 'payload': jsonEncode(payload),
  });

  @override
  Future<void> markFailed(int id, {required String error}) =>
      _update(id, <String, Object?>{'status': 'FAILED', 'last_error': error});

  @override
  Future<void> retry(int id) => _update(id, <String, Object?>{
    'status': 'PENDING',
    'next_attempt_at': null,
    'last_error': null,
  });

  Future<void> _update(int id, Map<String, Object?> values) async {
    final Database db = await _dbHelper.database;
    await db.update(_table, values, where: 'id = ?', whereArgs: <Object>[id]);
  }

  static OutboxItem _fromRow(Map<String, Object?> row) {
    final String? nextAttempt = row['next_attempt_at'] as String?;
    final Object? decoded = jsonDecode(row['payload'] as String);
    return OutboxItem(
      id: row['id'] as int,
      type: row['action_type'] as String,
      jobId: row['job_id'] as String?,
      payload: decoded is Map<String, Object?> ? decoded : <String, Object?>{},
      status: switch (row['status']) {
        'COMPLETED' => OutboxStatus.sent,
        'FAILED' => OutboxStatus.failed,
        _ => OutboxStatus.pending,
      },
      attempts: row['retry_count'] as int? ?? 0,
      createdAt: DateTime.parse(row['created_at'] as String),
      nextAttemptAt: nextAttempt == null ? null : DateTime.parse(nextAttempt),
      lastError: row['last_error'] as String?,
    );
  }
}
