import 'package:dio/dio.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/error/result.dart';
import '../models/standing.dart';

class WorkersRepository {
  final Dio _dio;

  WorkersRepository(this._dio);

  Future<Result<void, Failure>> registerSkill({
    required String trade,
    String? proofUrl,
  }) async {
    try {
      await _dio.post<Map<String, dynamic>>(
        '/workers/me/skills',
        data: {'trade': trade, if (proofUrl != null) 'proof_url': proofUrl},
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
        data: {'suburb': suburb, if (travelMeans != null) 'travel_means': travelMeans},
      );
      return const Ok(null);
    } on DioException catch (e) {
      return Error(_failureFor(e));
    }
  }

  Future<Result<Standing, Failure>> getStanding() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/workers/me/standing');
      return Ok(Standing.fromJson(response.data!));
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
