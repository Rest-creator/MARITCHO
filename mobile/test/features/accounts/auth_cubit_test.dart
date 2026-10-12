import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/core/storage/token_storage.dart';
import 'package:mobile/features/accounts/data/models/person.dart';
import 'package:mobile/features/accounts/data/repositories/auth_repository.dart';
import 'package:mobile/features/accounts/presentation/cubit/auth_cubit.dart';
import 'package:mobile/features/accounts/presentation/cubit/auth_state.dart';

class _FakeSuccessAuthRepository extends AuthRepository {
  _FakeSuccessAuthRepository() : super(Dio(), TokenStorage());

  @override
  Future<Result<Person, Failure>> login({
    required String phone,
    required String role,
  }) async {
    return Ok(Person(id: '1', phone: phone, role: role));
  }
}

class _FakeFailureAuthRepository extends AuthRepository {
  _FakeFailureAuthRepository() : super(Dio(), TokenStorage());

  @override
  Future<Result<Person, Failure>> login({
    required String phone,
    required String role,
  }) async {
    return const Error(NetworkFailure(message: 'Could not reach the server'));
  }
}

void main() {
  group('AuthCubit', () {
    test('starts in AuthInitial', () {
      final cubit = AuthCubit(_FakeSuccessAuthRepository());
      expect(cubit.state, isA<AuthInitial>());
      cubit.close();
    });

    test('ends in AuthSuccess with the logged-in Person when login succeeds', () async {
      final cubit = AuthCubit(_FakeSuccessAuthRepository());

      await cubit.login(phone: '+263771234567', role: 'WORKER');

      expect(cubit.state, isA<AuthSuccess>());
      expect((cubit.state as AuthSuccess).person.role, 'WORKER');
      await cubit.close();
    });

    test('ends in AuthFailure with the failure message when login fails', () async {
      final cubit = AuthCubit(_FakeFailureAuthRepository());

      await cubit.login(phone: '+263771234567', role: 'WORKER');

      expect(cubit.state, isA<AuthFailure>());
      expect((cubit.state as AuthFailure).errorMessage, 'Could not reach the server');
      await cubit.close();
    });
  });
}
