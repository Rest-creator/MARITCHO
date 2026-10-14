import 'dart:async';
import 'dart:io';
import 'dart:math';

import 'package:dio/dio.dart';

import 'package:mobile/core/sync/outbox.dart';
import 'package:mobile/core/sync/outbox_actions.dart';
import 'package:mobile/core/sync/outbox_item.dart';
import 'package:mobile/core/sync/sync_attempt.dart';
import 'package:mobile/core/sync/sync_report.dart';

/// Sends queued offline work to the backend.
///
/// Each item is tried once per pass. A failure never holds up the rest of
/// the queue: the item gets its own next-try time (30 s, doubling, at most
/// 15 min) and the pass moves on. A permanent refusal is kept with its
/// reason for the worker to see — work is never dropped silently.
class SyncService {
  final Outbox _outbox;
  final Dio _dio;
  final DateTime Function() _now;
  final Random _random;
  final Future<void> Function(String path) _removeFile;
  final StreamController<void> _changes = StreamController<void>.broadcast();

  bool _isSyncing = false;

  SyncService(
    this._outbox,
    this._dio, {
    DateTime Function()? now,
    Random? random,
    Future<void> Function(String path)? removeFile,
  }) : _now = now ?? DateTime.now,
       _random = random ?? Random(),
       _removeFile = removeFile ?? _deleteIfPresent;

  /// While uploads don't exist on the backend yet (issue #1), check hourly.
  static const Duration waitForMissingEndpoint = Duration(hours: 1);
  static const Duration _maxBackoff = Duration(minutes: 15);
  static const Duration _baseBackoff = Duration(seconds: 30);

  /// Fires after a pass that changed anything, so screens can refresh.
  Stream<void> get changes => _changes.stream;

  /// 30 s, 60 s, 2 min … capped at 15 min, plus up to 20 % jitter so a
  /// whole neighbourhood coming back online doesn't retry in lockstep.
  static Duration backoffFor(int attempts, Random random) {
    final int exponent = max(0, attempts - 1).clamp(0, 10);
    final int baseMs = min(
      _baseBackoff.inMilliseconds * (1 << exponent),
      _maxBackoff.inMilliseconds,
    );
    return Duration(milliseconds: baseMs + random.nextInt(baseMs ~/ 5 + 1));
  }

  /// Sends everything that is due. Never throws.
  Future<SyncReport> processQueue() async {
    if (_isSyncing) return const SyncReport.skipped();
    _isSyncing = true;
    int delivered = 0;
    int postponed = 0;
    int rejected = 0;
    try {
      final List<OutboxItem> due = await _outbox.due(_now());
      for (final OutboxItem item in due) {
        final SyncAttempt attempt = await _attempt(item);
        switch (attempt) {
          case Delivered():
            await _outbox.markSent(item.id);
            final Object? path = item.payload['file_path'];
            if (path is String) await _removeFile(path);
            delivered++;
          case RetryLater(
            :final String reason,
            :final Duration? after,
            :final payload,
          ):
            final int attempts = item.attempts + 1;
            await _outbox.reschedule(
              item.id,
              attempts: attempts,
              nextAttemptAt: _now().add(after ?? backoffFor(attempts, _random)),
              error: reason,
              payload: payload,
            );
            postponed++;
          case Rejected(:final String reason):
            await _outbox.markFailed(item.id, error: reason);
            rejected++;
        }
      }
    } on Object {
      // The database itself failed; try again on the next pass.
    } finally {
      _isSyncing = false;
    }
    final SyncReport report = SyncReport(
      delivered: delivered,
      postponed: postponed,
      rejected: rejected,
    );
    if (report.hasChanges && !_changes.isClosed) _changes.add(null);
    return report;
  }

  Future<SyncAttempt> _attempt(OutboxItem item) async {
    try {
      switch (item.type) {
        case OutboxActions.submitQuote:
          return await _sendQuote(item);
        case OutboxActions.sendPhoto:
          return await _sendPhoto(item);
        default:
          return Rejected(
            'This app version no longer knows how to send "${item.type}".',
          );
      }
    } on DioException catch (error) {
      return classify(error);
    } on FileSystemException {
      return const Rejected('The photo is no longer on this phone.');
    } on Object catch (error) {
      return RetryLater('Unexpected problem: $error');
    }
  }

  Future<SyncAttempt> _sendQuote(OutboxItem item) async {
    await _dio.post<Object?>(
      '/jobs/${item.jobId}/quote',
      data: <String, Object?>{
        'labor_amount': item.payload['labor_amount'],
        'materials_amount': item.payload['materials_amount'],
      },
    );
    return const Delivered();
  }

  Future<SyncAttempt> _sendPhoto(OutboxItem item) async {
    String? mediaUrl = item.payload['media_url'] as String?;
    if (mediaUrl == null) {
      final String path = item.payload['file_path'] as String;
      try {
        final Response<Object?> response = await _dio.post<Object?>(
          '/media',
          data: FormData.fromMap(<String, Object>{
            'kind': 'photo',
            // The backend checks the type and refuses a generic octet-stream.
            'file': await MultipartFile.fromFile(
              path,
              filename: 'photo.jpg',
              contentType: DioMediaType('image', 'jpeg'),
            ),
          }),
          options: Options(
            headers: <String, Object?>{
              'Idempotency-Key': item.payload['upload_key'],
            },
          ),
        );
        final Object? body = response.data;
        mediaUrl = body is Map<String, Object?> ? body['url'] as String? : null;
        if (mediaUrl == null) {
          return const RetryLater('The upload gave no address back.');
        }
      } on DioException catch (error) {
        final int? status = error.response?.statusCode;
        if (status == 404 || status == 405 || status == 501) {
          return const RetryLater(
            "Photos can't be sent yet. It will go once Maricho accepts them.",
            after: waitForMissingEndpoint,
          );
        }
        rethrow;
      }
    }

    try {
      await _dio.post<Object?>(
        '/jobs/${item.jobId}/messages',
        data: <String, Object?>{'message_type': 'PHOTO', 'media_url': mediaUrl},
      );
    } on DioException catch (error) {
      // Keep the upload: the retry only needs to send the chat message.
      final SyncAttempt outcome = classify(error);
      final Map<String, Object?> progressed = <String, Object?>{
        ...item.payload,
        'media_url': mediaUrl,
      };
      return switch (outcome) {
        RetryLater(:final String reason, :final Duration? after) => RetryLater(
          reason,
          after: after,
          payload: progressed,
        ),
        _ => outcome,
      };
    }
    return const Delivered();
  }

  /// What a failed request means for the queued work.
  static SyncAttempt classify(DioException error) {
    final int? status = error.response?.statusCode;
    if (status == null) {
      return const RetryLater(
        'No signal. It will send when you are connected.',
      );
    }
    if (status == 409) {
      return const Delivered(); // Already applied on the backend.
    }
    if (status == 401) {
      return const RetryLater(
        'Sign in again to send this.',
        after: Duration(minutes: 5),
      );
    }
    if (status == 429) {
      return const RetryLater('Maricho is busy.', after: Duration(minutes: 5));
    }
    if (status >= 500) {
      return const RetryLater('Maricho is having trouble. Trying again soon.');
    }
    return Rejected(
      _detailOf(error) ?? 'Maricho could not accept this (error $status).',
    );
  }

  static String? _detailOf(DioException error) {
    final Object? data = error.response?.data;
    if (data is Map<String, Object?>) {
      final Object? detail = data['detail'];
      if (detail is String && detail.trim().isNotEmpty) return detail;
      if (detail is List<Object?> && detail.isNotEmpty) {
        final Object? first = detail.first;
        if (first is Map<String, Object?> && first['msg'] is String) {
          return first['msg'] as String;
        }
      }
    }
    return null;
  }

  static Future<void> _deleteIfPresent(String path) async {
    try {
      final File file = File(path);
      if (await file.exists()) await file.delete();
    } on FileSystemException {
      // Already gone; nothing to tidy.
    }
  }

  Future<void> dispose() => _changes.close();
}
