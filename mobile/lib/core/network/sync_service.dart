import 'dart:convert';
import 'dart:math';
import 'package:dio/dio.dart';
import '../storage/database_helper.dart';

class SyncService {
  final DatabaseHelper _dbHelper;
  final Dio _dio;
  final _random = Random();
  
  bool _isSyncing = false;

  SyncService(this._dbHelper, this._dio);

  Future<void> processQueue() async {
    if (_isSyncing) return;
    _isSyncing = true;

    try {
      final actions = await _dbHelper.getPendingActions();
      
      for (var action in actions) {
        final id = action['id'] as int;
        final type = action['action_type'] as String;
        final payload = action['payload'] as String;
        final retryCount = action['retry_count'] as int;

        bool success = await _attemptSync(type, payload);

        if (success) {
          await _dbHelper.markActionCompleted(id);
        } else {
          await _dbHelper.incrementRetryCount(id, retryCount);
          // Apply exponential backoff with jitter
          // baseDelay * (2 ^ retryCount) + random_jitter
          final backoffMs = (1000 * pow(2, retryCount)).toInt();
          final jitter = _random.nextInt(1000);
          final delay = Duration(milliseconds: backoffMs + jitter);
          
          await Future.delayed(delay);
        }
      }
    } finally {
      _isSyncing = false;
    }
  }

  Future<bool> _attemptSync(String type, String payload) async {
    try {
      final data = jsonDecode(payload);
      
      switch (type) {
        case 'SYNC_CHECK_IN':
          final jobId = data['job_id'];
          // Make network request to the backend
          await _dio.post('/jobs/$jobId/check-in', data: data);
          return true;
        
        case 'SYNC_PHOTO_UPLOAD':
          final jobId = data['job_id'];
          final filePath = data['file_path'];
          
          final formData = FormData.fromMap({
            'type': data['type'],
            'timestamp': data['timestamp'],
            'file': await MultipartFile.fromFile(filePath, filename: filePath.split('/').last),
          });
          
          await _dio.post('/jobs/$jobId/photos', data: formData);
          
          // Mark the photo as synced in the local database
          final db = await _dbHelper.database;
          await db.update(
            'photo_uploads',
            {'synced': 1},
            where: 'id = ?',
            whereArgs: [data['photo_id']],
          );
          
          return true;
        
        default:
          return false;
      }
    } on DioException catch (e) {
      // Return false if it's a network/server issue.
      // If it's a 4xx error (like 400 Bad Request), you might want to drop it instead of retrying forever, 
      // but for "worker's worst day", we retain it or log a distinct failure.
      if (e.response?.statusCode != null && e.response!.statusCode! >= 400 && e.response!.statusCode! < 500) {
        // e.g. 409 Conflict, meaning already checked in. Safe to drop.
        if (e.response!.statusCode == 409) return true;
      }
      return false;
    } catch (e) {
      return false; // Unknown error, retain in queue
    }
  }
}
