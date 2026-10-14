import 'package:mobile/core/sync/outbox.dart';
import 'package:mobile/core/sync/outbox_item.dart';

/// An in-memory [Outbox] for tests: same behaviour as `SqliteOutbox`,
/// no database.
class FakeOutbox implements Outbox {
  final Map<int, OutboxItem> items = <int, OutboxItem>{};
  int _nextId = 1;

  @override
  Future<int> enqueue({
    required String type,
    required String? jobId,
    required Map<String, Object?> payload,
  }) async {
    final int id = _nextId++;
    items[id] = OutboxItem(
      id: id,
      type: type,
      jobId: jobId,
      payload: payload,
      status: OutboxStatus.pending,
      attempts: 0,
      createdAt: DateTime.utc(2026, 10, 14),
      nextAttemptAt: null,
      lastError: null,
    );
    return id;
  }

  @override
  Future<List<OutboxItem>> due(DateTime now) async =>
      items.values.where((OutboxItem item) => item.isDue(now)).toList()
        ..sort((OutboxItem a, OutboxItem b) => a.id.compareTo(b.id));

  @override
  Future<List<OutboxItem>> undeliveredForJob(String jobId) async => items.values
      .where(
        (OutboxItem item) =>
            item.jobId == jobId && item.status != OutboxStatus.sent,
      )
      .toList();

  @override
  Future<void> markSent(int id) async =>
      _replace(id, status: OutboxStatus.sent, lastError: null);

  @override
  Future<void> reschedule(
    int id, {
    required int attempts,
    required DateTime nextAttemptAt,
    required String? error,
    Map<String, Object?>? payload,
  }) async => _replace(
    id,
    attempts: attempts,
    nextAttemptAt: nextAttemptAt,
    lastError: error,
    payload: payload,
  );

  @override
  Future<void> markFailed(int id, {required String error}) async =>
      _replace(id, status: OutboxStatus.failed, lastError: error);

  @override
  Future<void> retry(int id) async => _replace(
    id,
    status: OutboxStatus.pending,
    clearNextAttempt: true,
    lastError: null,
  );

  void _replace(
    int id, {
    OutboxStatus? status,
    int? attempts,
    DateTime? nextAttemptAt,
    bool clearNextAttempt = false,
    String? lastError,
    Map<String, Object?>? payload,
  }) {
    final OutboxItem old = items[id]!;
    items[id] = OutboxItem(
      id: id,
      type: old.type,
      jobId: old.jobId,
      payload: payload ?? old.payload,
      status: status ?? old.status,
      attempts: attempts ?? old.attempts,
      createdAt: old.createdAt,
      nextAttemptAt: clearNextAttempt
          ? null
          : (nextAttemptAt ?? old.nextAttemptAt),
      lastError: lastError,
    );
  }
}
