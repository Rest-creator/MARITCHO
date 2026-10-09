import 'dart:convert';
import '../../../../core/error/failure.dart';
import '../../../../core/error/result.dart';
import '../../../../core/storage/database_helper.dart';

class CheckInRepository {
  final DatabaseHelper _dbHelper;

  CheckInRepository(this._dbHelper);

  Future<Result<void, Failure>> recordCheckIn({
    required String jobId,
    required String workerId,
    double? latitude,
    double? longitude,
  }) async {
    try {
      final timestamp = DateTime.now().toIso8601String();
      final checkInId = '\${jobId}_\${timestamp}';

      // 1. Save to specific check-in table
      final db = await _dbHelper.database;
      await db.insert('check_ins', {
        'id': checkInId,
        'job_id': jobId,
        'worker_id': workerId,
        'latitude': latitude,
        'longitude': longitude,
        'timestamp': timestamp,
        'synced': 0,
      });

      // 2. Queue the sync action
      final payload = jsonEncode({
        'job_id': jobId,
        'worker_id': workerId,
        'latitude': latitude,
        'longitude': longitude,
        'timestamp': timestamp,
      });

      await _dbHelper.insertOfflineAction('SYNC_CHECK_IN', payload);

      return const Ok(null);
    } catch (e) {
      return Error(StorageFailure(message: 'Failed to record check-in locally', exception: e as Exception));
    }
  }
}
