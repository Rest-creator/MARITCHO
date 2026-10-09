import 'dart:convert';
import '../../../../core/error/failure.dart';
import '../../../../core/error/result.dart';
import '../../../../core/storage/database_helper.dart';

class PhotoRepository {
  final DatabaseHelper _dbHelper;

  PhotoRepository(this._dbHelper);

  Future<Result<void, Failure>> queuePhotoUpload({
    required String jobId,
    required String filePath,
    required String photoType, // e.g., 'BEFORE' or 'AFTER'
  }) async {
    try {
      final timestamp = DateTime.now().toIso8601String();
      final photoId = '\${jobId}_\${photoType}_\${timestamp}';

      // Save locally
      final db = await _dbHelper.database;
      await db.insert('photo_uploads', {
        'id': photoId,
        'job_id': jobId,
        'file_path': filePath,
        'type': photoType,
        'timestamp': timestamp,
        'synced': 0,
      });

      // Queue sync action
      final payload = jsonEncode({
        'photo_id': photoId,
        'job_id': jobId,
        'file_path': filePath,
        'type': photoType,
        'timestamp': timestamp,
      });

      await _dbHelper.insertOfflineAction('SYNC_PHOTO_UPLOAD', payload);

      return const Ok(null);
    } catch (e) {
      return Error(StorageFailure(message: 'Failed to queue photo upload locally', exception: e as Exception));
    }
  }
}
