import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/features/accounts/data/repositories/account_repository.dart';
import 'package:mobile/features/accounts/presentation/cubit/account_state.dart';

class AccountCubit extends Cubit<AccountState> {
  final AccountRepository _repository;

  AccountCubit(this._repository) : super(const AccountInitial());

  Future<void> loadProfile() async {
    emit(const AccountLoading());
    final result = await _repository.getCurrentUser();
    result.match(
      onOk: (person) => emit(AccountLoaded(person: person)),
      onError: (failure) => emit(AccountFailure(errorMessage: failure.message)),
    );
  }

  Future<bool> updateProfile({
    String? displayName,
    String? role,
    bool? isAvailable,
    int? travelKm,
    String? homeSuburb,
    String? nextOfKinPhone,
  }) async {
    final currentState = state;
    if (currentState is! AccountLoaded) return false;

    emit(currentState.copyWith(isSaving: true, clearNotice: true));
    final result = await _repository.updateProfile(
      displayName: displayName,
      role: role,
      isAvailable: isAvailable,
      travelKm: travelKm,
      homeSuburb: homeSuburb,
      nextOfKinPhone: nextOfKinPhone,
    );

    return result.fold<bool>(
      onOk: (updatedPerson) {
        emit(
          currentState.copyWith(
            person: updatedPerson,
            isSaving: false,
            noticeMessage: 'Profile updated successfully',
          ),
        );
        return true;
      },
      onError: (failure) {
        emit(
          currentState.copyWith(
            isSaving: false,
            noticeMessage: failure.message,
          ),
        );
        return false;
      },
    );
  }

  Future<bool> switchRole(String newRole) async {
    return updateProfile(role: newRole);
  }
}
