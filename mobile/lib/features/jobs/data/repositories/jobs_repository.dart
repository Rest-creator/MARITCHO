import 'package:dio/dio.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/error/result.dart';
import '../models/job.dart';
import '../models/match_candidate.dart';
import '../models/my_offer.dart';
import '../models/open_job.dart';

class JobsRepository {
  final Dio _dio;

  JobsRepository(this._dio);

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
    return _call(() async {
      final response = await _dio.get<List<dynamic>>('/jobs/mine');
      return response.data!.map((json) => Job.fromJson(json as Map<String, dynamic>)).toList();
    });
  }

  Future<Result<List<MatchCandidate>, Failure>> getMatches(String jobId) {
    return _call(() async {
      final response = await _dio.get<List<dynamic>>('/jobs/$jobId/matches');
      return response.data!
          .map((json) => MatchCandidate.fromJson(json as Map<String, dynamic>))
          .toList();
    });
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
    return _call(() async {
      final response = await _dio.get<List<dynamic>>('/jobs/open');
      return response.data!.map((json) => OpenJob.fromJson(json as Map<String, dynamic>)).toList();
    });
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
      final data = e.response?.data;
      final detail = data is Map ? data['detail'] : null;
      return Error(
        NetworkFailure(
          message: detail?.toString() ?? e.message ?? 'Could not reach the server',
          exception: e,
        ),
      );
    }
  }

  Future<Result<List<Job>, Failure>> listAssigned() {
    return _call(() async {
      final response = await _dio.get<List<dynamic>>('/jobs/assigned');
      return response.data!.map((json) => Job.fromJson(json as Map<String, dynamic>)).toList();
    });
  }

  Future<Result<List<MyOffer>, Failure>> listMyOffers() {
    return _call(() async {
      final response = await _dio.get<List<dynamic>>('/jobs/my-offers');
      return response.data!.map((json) => MyOffer.fromJson(json as Map<String, dynamic>)).toList();
    });
  }

  Future<Result<T, Failure>> _call<T>(Future<T> Function() request) async {
    try {
      return Ok(await request());
    } on DioException catch (e) {
      final data = e.response?.data;
      final detail = data is Map ? data['detail'] : null;
      return Error(
        NetworkFailure(
          message: detail?.toString() ?? e.message ?? 'Could not reach the server',
          exception: e,
        ),
      );
    }
  }
}
