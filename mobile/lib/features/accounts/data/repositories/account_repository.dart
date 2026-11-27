import 'package:dio/dio.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/features/accounts/data/models/person.dart';

class AccountRepository {
  final Dio _dio;

  AccountRepository(this._dio);

  Future<Result<Person, Failure>> getCurrentUser() async {
    try {
      final Response<Map<String, dynamic>> response = await _dio
          .get<Map<String, dynamic>>('/users/me');
      return Ok(Person.fromJson(response.data!));
    } on DioException catch (error) {
      return Error(_failureFor(error));
    } on Object catch (error) {
      return Error(
        UnknownFailure(
          message: 'Could not load profile',
          exception: error is Exception ? error : Exception(error.toString()),
        ),
      );
    }
  }

  Future<Result<Person, Failure>> updateProfile({
    String? displayName,
    String? role,
    bool? isAvailable,
    int? travelKm,
    String? homeSuburb,
    String? nextOfKinPhone,
  }) async {
    try {
      final Map<String, dynamic> payload = <String, dynamic>{};
      if (displayName != null) payload['display_name'] = displayName;
      if (role != null) payload['role'] = role;
      if (isAvailable != null) payload['is_available'] = isAvailable;
      if (travelKm != null) payload['travel_km'] = travelKm;
      if (homeSuburb != null) payload['home_suburb'] = homeSuburb;
      if (nextOfKinPhone != null) payload['next_of_kin_phone'] = nextOfKinPhone;

      final Response<Map<String, dynamic>> response = await _dio
          .patch<Map<String, dynamic>>('/users/me', data: payload);
      return Ok(Person.fromJson(response.data!));
    } on DioException catch (error) {
      return Error(_failureFor(error));
    } on Object catch (error) {
      return Error(
        UnknownFailure(
          message: 'Could not update profile',
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
          detail?.toString() ??
          error.message ??
          'Could not complete account request',
      exception: error,
    );
  }
}
