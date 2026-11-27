import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/error/result.dart';
import '../../../../core/storage/database_helper.dart';
import '../models/standing.dart';
import '../models/worker_directory_item.dart';
import '../models/worker_vetting.dart';

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

  Future<Result<WorkerVetting, Failure>> getVetting() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/workers/me/vetting',
      );
      return Ok(WorkerVetting.fromJson(response.data!));
    } on DioException catch (e) {
      return Error(_failureFor(e));
    } on Object catch (e) {
      return Error(
        UnknownFailure(
          message: 'Could not load vetting status',
          exception: e is Exception ? e : Exception(e.toString()),
        ),
      );
    }
  }

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

  Future<Result<List<WorkerDirectoryItem>, Failure>> listNearbyWorkers({
    String? suburb,
    String? trade,
    String? query,
    int limit = 50,
    int offset = 0,
  }) async {
    try {
      final Map<String, dynamic> params = {'limit': limit, 'offset': offset};
      if (suburb != null && suburb.isNotEmpty) params['suburb'] = suburb;
      if (trade != null && trade.isNotEmpty) params['trade'] = trade;
      if (query != null && query.isNotEmpty) params['q'] = query;

      final response = await _dio.get<List<dynamic>>(
        '/workers',
        queryParameters: params,
      );
      final items = (response.data ?? [])
          .map((e) => WorkerDirectoryItem.fromJson(e as Map<String, dynamic>))
          .toList();
      return Ok(items);
    } on DioException catch (e) {
      return Error(_failureFor(e));
    } on Object catch (e) {
      return Error(
        UnknownFailure(
          message: 'Could not load workers directory',
          exception: e is Exception ? e : Exception(e.toString()),
        ),
      );
    }
  }

  Future<Result<WorkerPublicProfile, Failure>> getWorkerProfile(
    String workerId, {
    String? suburb,
  }) async {
    try {
      final Map<String, dynamic> params = {};
      if (suburb != null && suburb.isNotEmpty) params['suburb'] = suburb;

      final response = await _dio.get<Map<String, dynamic>>(
        '/workers/$workerId',
        queryParameters: params,
      );
      return Ok(WorkerPublicProfile.fromJson(response.data!));
    } on DioException catch (e) {
      return Error(_failureFor(e));
    } on Object catch (e) {
      return Error(
        UnknownFailure(
          message: 'Could not load worker profile',
          exception: e is Exception ? e : Exception(e.toString()),
        ),
      );
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
