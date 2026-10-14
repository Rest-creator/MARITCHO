import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/features/accounts/data/models/code_request.dart';
import 'package:mobile/features/accounts/data/models/person.dart';
import 'package:mobile/features/accounts/data/repositories/auth_repository.dart';
import 'package:mobile/features/accounts/presentation/cubit/auth_state.dart';

/// Sign-up / sign-in: phone number first, then the 6-digit code if one was
/// sent (WEB-005's flow, through the BFF).
class AuthCubit extends Cubit<AuthState> {
  final AuthRepository _authRepository;
  String _phone = '';
  String _role = 'BUYER';

  AuthCubit(this._authRepository) : super(AuthInitial());

  /// Ask for a code; sign straight in when the backend can't send one.
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

  /// Back to the phone-number form.
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
}
