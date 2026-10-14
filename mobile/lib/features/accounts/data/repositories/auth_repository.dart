import 'package:dio/dio.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/error/result.dart';
import '../../../../core/storage/token_storage.dart';
import '../models/person.dart';

/// Mock login (see backend ADR-006 / backlog BACK-009): the server only
/// checks the phone number, no real OTP verification yet — `role` is
/// only honored the first time this phone number logs in.
class AuthRepository {
  final Dio _dio;
  final TokenStorage _tokenStorage;

  AuthRepository(this._dio, this._tokenStorage);

  Future<Result<Person, Failure>> login({
    required String phone,
    required String role,
  }) async {
    try {
      final tokenResponse = await _dio.post<Map<String, dynamic>>(
        '/token',
        data: {'username': phone, 'password': '', 'role': role},
        options: Options(contentType: Headers.formUrlEncodedContentType),
      );

      final accessToken = tokenResponse.data!['access_token'] as String;
      await _tokenStorage.saveToken(accessToken);

      final meResponse = await _dio.get<Map<String, dynamic>>('/users/me');
      return Ok(Person.fromJson(meResponse.data!));
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
    } catch (e) {
      return Error(
        UnknownFailure(
          message: 'Something went wrong signing in',
          exception: e is Exception ? e : Exception(e.toString()),
        ),
      );
    }
  }
}
