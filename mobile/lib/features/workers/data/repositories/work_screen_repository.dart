import 'dart:convert';

import 'package:dio/dio.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/core/storage/database_helper.dart';
import 'package:mobile/features/workers/data/models/work_screen.dart';

/// "My work" in one request instead of three made one after another —
/// on a slow connection that's two round trips saved every time the
/// screen opens. Offline, the last good copy is shown.
class WorkScreenRepository {
  final Dio _dio;
  final DatabaseHelper _dbHelper;

  WorkScreenRepository(this._dio, this._dbHelper);

  static const String _cacheKey = 'screens.workerWork';

  Future<Result<WorkScreen, Failure>> load() async {
    try {
      final Response<Map<String, dynamic>> response = await _dio
          .get<Map<String, dynamic>>('/screens/worker-work');
      final Map<String, dynamic> body = response.data!;
      final WorkScreen screen = WorkScreen.fromJson(body);
      await _dbHelper.cacheResponse(_cacheKey, jsonEncode(body));
      return Ok(screen);
    } on DioException catch (error) {
      final String? cached = await _dbHelper.getCachedResponse(_cacheKey);
      if (cached != null) {
        return Ok(
          WorkScreen.fromJson(jsonDecode(cached) as Map<String, dynamic>),
        );
      }
      final Object? data = error.response?.data;
      final Object? detail = data is Map ? data['detail'] : null;
      return Error(
        NetworkFailure(
          message:
              detail?.toString() ?? error.message ?? 'Could not reach Maricho',
          exception: error,
        ),
      );
    } on Object {
      return const Error(UnknownFailure(message: 'Could not read your work.'));
    }
  }
}
