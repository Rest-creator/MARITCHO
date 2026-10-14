import 'package:mobile/core/sync/outbox_item.dart';

/// The phone's outbound queue: work done offline waits here until the
/// backend has it. An interface so `SyncService` can be tested without a
/// database (`SqliteOutbox` is the real one).
abstract class Outbox {
  /// Saves an action; returns its id.
  Future<int> enqueue({
    required String type,
    required String? jobId,
    required Map<String, Object?> payload,
  });

  /// Pending actions whose retry time has come, oldest first.
  Future<List<OutboxItem>> due(DateTime now);

  /// Everything not yet delivered for [jobId] (pending and failed), so the
  /// screen can say "saved, sends when there's signal" or why it failed.
  Future<List<OutboxItem>> undeliveredForJob(String jobId);

  Future<void> markSent(int id);

  /// Try again at [nextAttemptAt]; [payload] replaces the stored one when
  /// a multi-step action has made progress (e.g. the photo is uploaded).
  Future<void> reschedule(
    int id, {
    required int attempts,
    required DateTime nextAttemptAt,
    required String? error,
    Map<String, Object?>? payload,
  });

  Future<void> markFailed(int id, {required String error});

  /// Put a failed action back in line (the worker tapped "Try again").
  Future<void> retry(int id);
}
