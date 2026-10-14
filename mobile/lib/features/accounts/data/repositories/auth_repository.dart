import 'package:dio/dio.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/core/storage/token_storage.dart';
import 'package:mobile/features/accounts/data/models/code_request.dart';
import 'package:mobile/features/accounts/data/models/person.dart';

/// Sign-in through the BFF (ADR-009), the same two steps as the website:
/// ask for a 6-digit code, then sign in with it. While the backend can't
/// send codes yet, the BFF says so and sign-in goes ahead without one.
class AuthRepository {
  final Dio _dio;
  final TokenStorage _tokenStorage;

  AuthRepository(this._dio, this._tokenStorage);

  /// Tells the BFF this is the app, so sign-in returns the token in the
  /// response instead of setting a browser cookie.
  static const Map<String, String> _mobileClient = <String, String>{
    'X-Maricho-Client': 'mobile',
  };

  /// "07 74 123 089", "774123089" or "+263 77 412 3089" → "+263774123089".
  static String normalisePhone(String input, {String countryCode = '263'}) {
    final String digits = input.replaceAll(RegExp(r'\D'), '');
    if (digits.startsWith(countryCode)) return '+$digits';
    return '+$countryCode${digits.replaceFirst(RegExp(r'^0+'), '')}';
  }

  Future<Result<CodeRequest, Failure>> requestCode({
    required String phone,
  }) async {
    try {
      final Response<Map<String, dynamic>> response = await _dio
          .post<Map<String, dynamic>>(
            '/session/code',
            data: <String, Object?>{'phone': phone},
          );
      return Ok(CodeRequest.fromJson(response.data!));
    } on DioException catch (error) {
      return Error(_failureFor(error));
    }
  }

  Future<Result<Person, Failure>> login({
    required String phone,
    required String role,
    String? code,
  }) async {
    try {
      final Response<Map<String, dynamic>> response = await _dio
          .post<Map<String, dynamic>>(
            '/session',
            data: <String, Object?>{
              'phone': phone,
              'role': role,
              'code': ?code,
            },
            options: Options(headers: _mobileClient),
          );
      final Map<String, dynamic> body = response.data!;
      await _tokenStorage.saveToken(body['access_token'] as String);
      return Ok(Person.fromJson(body['user'] as Map<String, dynamic>));
    } on DioException catch (error) {
      return Error(_failureFor(error));
    } on Object catch (error) {
      return Error(
        UnknownFailure(
          message: 'Something went wrong signing in',
          exception: error is Exception ? error : Exception(error.toString()),
        ),
      );
    }
  }

  Failure _failureFor(DioException error) {
    final Object? data = error.response?.data;
    final Object? detail = data is Map ? data['detail'] : null;
    return NetworkFailure(
      message: detail?.toString() ?? error.message ?? 'Could not reach Maricho',
      exception: error,
    );
  }
}
