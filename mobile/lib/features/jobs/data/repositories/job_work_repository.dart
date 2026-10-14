import 'dart:io';
import 'dart:math';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/core/sync/outbox.dart';
import 'package:mobile/core/sync/outbox_actions.dart';
import 'package:mobile/core/sync/outbox_item.dart';

/// Work a hired worker does on site, saved on the phone first and sent by
/// `SyncService` when there is signal (APP-002): the price confirmed on
/// arrival, and photos of the job.
class JobWorkRepository {
  final Outbox _outbox;
  final void Function() _onQueued;
  final Future<Directory> Function() _photoDirectory;
  final Random _random;

  JobWorkRepository(
    this._outbox, {
    required this._onQueued,
    required this._photoDirectory,
    Random? random,
  }) : _random = random ?? Random.secure();

  /// "I've arrived": queue the price confirmed on site.
  Future<Result<void, Failure>> queueQuote({
    required String jobId,
    required double laborAmount,
    required double materialsAmount,
  }) async {
    if (!laborAmount.isFinite || laborAmount <= 0) {
      return const Error(
        ValidationFailure(message: 'Enter what your work costs.'),
      );
    }
    if (!materialsAmount.isFinite || materialsAmount < 0) {
      return const Error(
        ValidationFailure(message: 'Materials can be 0, but not less.'),
      );
    }
    return _enqueue(
      type: OutboxActions.submitQuote,
      jobId: jobId,
      payload: <String, Object?>{
        'job_id': jobId,
        'labor_amount': _cents(laborAmount),
        'materials_amount': _cents(materialsAmount),
      },
    );
  }

  /// Queue a photo of the job. The camera's temporary file is copied into
  /// the app's own storage first, so it survives until it has been sent.
  Future<Result<void, Failure>> queuePhoto({
    required String jobId,
    required String sourcePath,
  }) async {
    final String uploadKey = _newKey();
    final String keptPath;
    try {
      final Directory directory = await _photoDirectory();
      await directory.create(recursive: true);
      keptPath = '${directory.path}${Platform.pathSeparator}$uploadKey.jpg';
      await File(sourcePath).copy(keptPath);
    } on FileSystemException catch (error) {
      return Error(
        StorageFailure(
          message: 'Could not keep the photo on this phone.',
          exception: error,
        ),
      );
    }
    return _enqueue(
      type: OutboxActions.sendPhoto,
      jobId: jobId,
      payload: <String, Object?>{
        'job_id': jobId,
        'file_path': keptPath,
        'upload_key': uploadKey,
      },
    );
  }

  /// What is still waiting to send (or was refused) for [jobId].
  Future<Result<List<OutboxItem>, Failure>> undelivered(String jobId) async {
    try {
      return Ok(await _outbox.undeliveredForJob(jobId));
    } on Object {
      return const Error(
        StorageFailure(message: 'Could not read what is waiting to send.'),
      );
    }
  }

  /// Try a refused item again (after the worker fixed the problem).
  Future<Result<void, Failure>> retry(int id) async {
    try {
      await _outbox.retry(id);
      _onQueued();
      return const Ok(null);
    } on Object {
      return const Error(StorageFailure(message: 'Could not try again.'));
    }
  }

  Future<Result<void, Failure>> _enqueue({
    required String type,
    required String jobId,
    required Map<String, Object?> payload,
  }) async {
    try {
      await _outbox.enqueue(type: type, jobId: jobId, payload: payload);
    } on Object {
      return const Error(
        StorageFailure(message: 'Could not save this on the phone.'),
      );
    }
    _onQueued();
    return const Ok(null);
  }

  /// Money is rounded to whole cents, as the backend stores it (2 places).
  static double _cents(double amount) => (amount * 100).roundToDouble() / 100;

  String _newKey() {
    final StringBuffer buffer = StringBuffer();
    for (int i = 0; i < 16; i++) {
      buffer.write(_random.nextInt(256).toRadixString(16).padLeft(2, '0'));
    }
    return buffer.toString();
  }
}
