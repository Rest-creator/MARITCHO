import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/error/result.dart';
import '../../../../core/storage/database_helper.dart';
import '../models/job.dart';
import '../models/match_candidate.dart';
import '../models/my_offer.dart';
import '../models/open_job.dart';

class JobsRepository {
  final Dio _dio;
  final DatabaseHelper _dbHelper;

  JobsRepository(this._dio, this._dbHelper);

  Future<Result<Job, Failure>> createJob({
    required String trade,
    required String suburb,
    required String address,
    required String problemDescription,
    double? budgetAmount,
  }) {
    return _call(() async {
      final response = await _dio.post<Map<String, dynamic>>(
        '/jobs/request',
        data: {
          'trade': trade,
          'suburb': suburb,
          'address': address,
          'problem_description': problemDescription,
          if (budgetAmount != null) 'budget_amount': budgetAmount,
        },
      );
      return Job.fromJson(response.data!);
    });
  }

  Future<Result<List<Job>, Failure>> listMine() {
    return _cachedList(cacheKey: 'jobs.listMine', path: '/jobs/mine', fromJson: Job.fromJson);
  }

  Future<Result<List<MatchCandidate>, Failure>> getMatches(String jobId) {
    return _cachedList(
      cacheKey: 'jobs.matches.$jobId',
      path: '/jobs/$jobId/matches',
      fromJson: MatchCandidate.fromJson,
    );
  }

  Future<Result<Job, Failure>> bookJob({
    required String jobId,
    required String workerId,
    required double depositAmount,
    String currency = 'USD',
  }) {
    return _call(() async {
      final response = await _dio.post<Map<String, dynamic>>(
        '/jobs/$jobId/book',
        data: {'worker_id': workerId, 'deposit_amount': depositAmount, 'currency': currency},
      );
      return Job.fromJson(response.data!);
    });
  }

  Future<Result<Job, Failure>> completeJob({
    required String jobId,
    required String whatWasDone,
    String? clientWords,
  }) {
    return _call(() async {
      final response = await _dio.post<Map<String, dynamic>>(
        '/jobs/$jobId/complete',
        data: {'what_was_done': whatWasDone, if (clientWords != null) 'client_words': clientWords},
      );
      return Job.fromJson(response.data!);
    });
  }

  Future<Result<List<OpenJob>, Failure>> listOpen() {
    return _cachedList(cacheKey: 'jobs.listOpen', path: '/jobs/open', fromJson: OpenJob.fromJson);
  }

  Future<Result<void, Failure>> submitOffer({
    required String jobId,
    required double quotedAmount,
    String? availabilityNote,
  }) async {
    try {
      await _dio.post<Map<String, dynamic>>(
        '/jobs/$jobId/offers',
        data: {
          'quoted_amount': quotedAmount,
          if (availabilityNote != null) 'availability_note': availabilityNote,
        },
      );
      return const Ok(null);
    } on DioException catch (e) {
      return Error(_failureFor(e));
    }
  }

  Future<Result<List<Job>, Failure>> listAssigned() {
    return _cachedList(cacheKey: 'jobs.listAssigned', path: '/jobs/assigned', fromJson: Job.fromJson);
  }

  Future<Result<List<MyOffer>, Failure>> listMyOffers() {
    return _cachedList(
      cacheKey: 'jobs.listMyOffers',
      path: '/jobs/my-offers',
      fromJson: MyOffer.fromJson,
    );
  }

  /// Offline-first read: fetch, cache the raw payload on success, and —
  /// if the live fetch fails (no connectivity, backend unreachable) — fall
  /// back to the last cached payload instead of surfacing an empty screen.
  /// Mirrors the Mobile App Agent-First Development Guide's "Abstracting
  /// the Offline Data Layer" pattern (try remote, fall back to local cache
  /// on failure), applied to every list-reading endpoint in this repository.
  Future<Result<List<T>, Failure>> _cachedList<T>({
    required String cacheKey,
    required String path,
    required T Function(Map<String, dynamic>) fromJson,
  }) async {
    try {
      final response = await _dio.get<List<dynamic>>(path);
      final raw = response.data!;
      await _dbHelper.cacheResponse(cacheKey, jsonEncode(raw));
      return Ok(raw.map((json) => fromJson(json as Map<String, dynamic>)).toList());
    } on DioException catch (e) {
      final cached = await _dbHelper.getCachedResponse(cacheKey);
      if (cached != null) {
        final raw = jsonDecode(cached) as List<dynamic>;
        return Ok(raw.map((json) => fromJson(json as Map<String, dynamic>)).toList());
      }
      return Error(_failureFor(e));
    }
  }

  Future<Result<T, Failure>> _call<T>(Future<T> Function() request) async {
    try {
      return Ok(await request());
    } on DioException catch (e) {
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
