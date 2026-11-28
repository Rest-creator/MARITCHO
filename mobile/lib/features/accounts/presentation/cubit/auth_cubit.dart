import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/features/accounts/data/models/code_request.dart';
import 'package:mobile/features/accounts/data/models/person.dart';
import 'package:mobile/features/accounts/data/repositories/auth_repository.dart';
import 'package:mobile/features/accounts/presentation/cubit/auth_state.dart';

/// Sign-up & sign-in with phone + password or code through the BFF.
class AuthCubit extends Cubit<AuthState> {
  final AuthRepository _authRepository;
  String _phone = '';
  String _role = 'BUYER';

  AuthCubit(this._authRepository) : super(AuthInitial());

  /// Sign in with existing phone and password.
  Future<void> signIn({required String phone, required String password}) async {
    emit(AuthLoading());
    final Result<Person, Failure> result = await _authRepository.signIn(
      phone: phone,
      password: password,
    );
    if (result.isOk) {
      emit(AuthSuccess(result.okValue));
    } else {
      emit(AuthFailure(result.errorValue.message));
    }
  }

  /// Sign up with phone, password, name, and role.
  Future<void> signUp({
    required String phone,
    required String password,
    required String name,
    required String role,
  }) async {
    emit(AuthLoading());
    final Result<Person, Failure> result = await _authRepository.signUp(
      phone: phone,
      password: password,
      name: name,
      role: role,
    );
    if (result.isOk) {
      emit(AuthSuccess(result.okValue));
    } else {
      emit(AuthFailure(result.errorValue.message));
    }
  }

  /// OTP / Code compatibility start flow.
  Future<void> start({required String phone, required String role}) async {
    _phone = AuthRepository.normalisePhone(phone);
    _role = role;
    emit(AuthLoading());
    final Result<CodeRequest, Failure> request = await _authRepository
        .requestCode(phone: _phone);
    if (request.isError) {
      emit(AuthFailure(request.errorValue.message));
      return;
    }
    if (request.okValue.isCodeRequired) {
      emit(AuthCodeRequired(phone: _phone));
      return;
    }
    await _signIn(code: null);
  }

  Future<void> verify(String code) async {
    emit(AuthCodeRequired(phone: _phone, isVerifying: true));
    await _signIn(code: code);
  }

  Future<void> resend() async {
    final Result<CodeRequest, Failure> request = await _authRepository
        .requestCode(phone: _phone);
    emit(
      AuthCodeRequired(
        phone: _phone,
        errorMessage: request.isError ? request.errorValue.message : null,
      ),
    );
  }

  void changeNumber() => emit(AuthInitial());

  Future<void> _signIn({required String? code}) async {
    final Result<Person, Failure> result = await _authRepository.login(
      phone: _phone,
      role: _role,
      code: code,
    );
    if (result.isOk) {
      emit(AuthSuccess(result.okValue));
    } else if (code != null) {
      emit(
        AuthCodeRequired(
          phone: _phone,
          errorMessage: result.errorValue.message,
        ),
      );
    } else {
      emit(AuthFailure(result.errorValue.message));
    }
  }

  void reset() => emit(AuthInitial());
}
