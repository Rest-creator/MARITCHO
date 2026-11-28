import 'package:dio/dio.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/core/storage/token_storage.dart';
import 'package:mobile/features/accounts/data/models/code_request.dart';
import 'package:mobile/features/accounts/data/models/person.dart';

/// Sign-in & sign-up through the BFF (ADR-009 / `frontend/src/app/api/session/route.ts`).
class AuthRepository {
  final Dio _dio;
  final TokenStorage _tokenStorage;

  AuthRepository(this._dio, this._tokenStorage);

  static const Map<String, String> _mobileClient = <String, String>{
    'X-Maricho-Client': 'mobile',
  };

  /// "07 74 123 089", "774123089" or "+263 77 412 3089" → "+263774123089".
  static String normalisePhone(String input, {String countryCode = '263'}) {
    final String digits = input.replaceAll(RegExp(r'\D'), '');
    if (digits.startsWith(countryCode)) return '+$digits';
    return '+$countryCode${digits.replaceFirst(RegExp(r'^0+'), '')}';
  }

  /// Request code (for OTP flows / backward compatibility).
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

  /// Sign in with an existing account's phone and password.
  Future<Result<Person, Failure>> signIn({
    required String phone,
    required String password,
  }) async {
    return _authenticate(
      payload: <String, Object?>{
        'mode': 'signin',
        'phone': normalisePhone(phone),
        'password': password,
      },
    );
  }

  /// Create a new account with phone, password, name, and role.
  Future<Result<Person, Failure>> signUp({
    required String phone,
    required String password,
    required String name,
    required String role,
  }) async {
    return _authenticate(
      payload: <String, Object?>{
        'mode': 'signup',
        'phone': normalisePhone(phone),
        'password': password,
        'name': name.isEmpty ? 'User' : name,
        'role': role,
      },
    );
  }

  /// Login compatibility method (used by tests and existing OTP code flows).
  Future<Result<Person, Failure>> login({
    required String phone,
    required String role,
    String? code,
  }) async {
    return _authenticate(
      payload: <String, Object?>{'phone': phone, 'role': role, 'code': ?code},
    );
  }

  Future<Result<Person, Failure>> _authenticate({
    required Map<String, Object?> payload,
  }) async {
    try {
      final Response<Map<String, dynamic>> response = await _dio
          .post<Map<String, dynamic>>(
            '/session',
            data: payload,
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
      message:
          detail?.toString() ?? error.message ?? 'Could not reach Maritcho',
      exception: error,
    );
  }
}
