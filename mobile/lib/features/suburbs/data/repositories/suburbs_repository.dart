import 'package:dio/dio.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/error/result.dart';
import '../models/suburb.dart';

class SuburbsRepository {
  final Dio _dio;

  SuburbsRepository(this._dio);

  Future<Result<List<Suburb>, Failure>> listSuburbs() async {
    try {
      final response = await _dio.get<List<dynamic>>(
        '/suburbs',
        queryParameters: {'limit': 200},
      );
      final suburbs = response.data!
          .map((json) => Suburb.fromJson(json as Map<String, dynamic>))
          .toList();
      return Ok(suburbs);
    } on DioException catch (e) {
      final data = e.response?.data;
      final detail = data is Map ? data['detail'] : null;
      return Error(
        NetworkFailure(
          message:
              detail?.toString() ?? e.message ?? 'Could not reach the server',
          exception: e,
        ),
      );
    }
  }
}
