import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/auth_repository.dart';
import 'auth_state.dart';

class AuthCubit extends Cubit<AuthState> {
  final AuthRepository _authRepository;

  AuthCubit(this._authRepository) : super(AuthInitial());

  Future<void> login({required String phone, required String role}) async {
    emit(AuthLoading());

    final result = await _authRepository.login(phone: phone, role: role);

    result.fold(
      onOk: (person) => emit(AuthSuccess(person)),
      onError: (failure) => emit(AuthFailure(failure.message)),
    );
  }
}
