import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/error/result.dart';
import '../../../../core/storage/database_helper.dart';
import '../models/standing.dart';

class WorkersRepository {
  final Dio _dio;
  final DatabaseHelper _dbHelper;

  WorkersRepository(this._dio, this._dbHelper);

  Future<Result<void, Failure>> registerSkill({
    required String trade,
    String? proofUrl,
  }) async {
    try {
      await _dio.post<Map<String, dynamic>>(
        '/workers/me/skills',
        data: {'trade': trade, 'proof_url': ?proofUrl},
      );
      return const Ok(null);
    } on DioException catch (e) {
      return Error(_failureFor(e));
    }
  }

  Future<Result<void, Failure>> registerServiceArea({
    required String suburb,
    String? travelMeans,
  }) async {
    try {
      await _dio.post<Map<String, dynamic>>(
        '/workers/me/service-areas',
        data: {'suburb': suburb, 'travel_means': ?travelMeans},
      );
      return const Ok(null);
    } on DioException catch (e) {
      return Error(_failureFor(e));
    }
  }

  /// Offline-first read, same cache-aside pattern as JobsRepository: try the
  /// network first, cache the payload on success, and fall back to the last
  /// cached standing if the live fetch fails.
  Future<Result<Standing, Failure>> getStanding() async {
    const cacheKey = 'workers.standing';
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/workers/me/standing',
      );
      final raw = response.data!;
      await _dbHelper.cacheResponse(cacheKey, jsonEncode(raw));
      return Ok(Standing.fromJson(raw));
    } on DioException catch (e) {
      final cached = await _dbHelper.getCachedResponse(cacheKey);
      if (cached != null) {
        return Ok(
          Standing.fromJson(jsonDecode(cached) as Map<String, dynamic>),
        );
      }
      return Error(_failureFor(e));
    }
  }

  Failure _failureFor(DioException e) {
    final data = e.response?.data;
    final detail = data is Map ? data['detail'] : null;
    return NetworkFailure(
      message: detail?.toString() ?? e.message ?? 'Could not reach the server',
      exception: e,
    );
  }
}
