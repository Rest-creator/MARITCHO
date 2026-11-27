import 'package:equatable/equatable.dart';

import 'package:mobile/features/accounts/data/models/person.dart';

abstract class AccountState extends Equatable {
  const AccountState();

  @override
  List<Object?> get props => [];
}

class AccountInitial extends AccountState {
  const AccountInitial();
}

class AccountLoading extends AccountState {
  const AccountLoading();
}

class AccountLoaded extends AccountState {
  final Person person;
  final bool isSaving;
  final String? noticeMessage;

  const AccountLoaded({
    required this.person,
    this.isSaving = false,
    this.noticeMessage,
  });

  AccountLoaded copyWith({
    Person? person,
    bool? isSaving,
    String? noticeMessage,
    bool clearNotice = false,
  }) {
    return AccountLoaded(
      person: person ?? this.person,
      isSaving: isSaving ?? this.isSaving,
      noticeMessage: clearNotice ? null : (noticeMessage ?? this.noticeMessage),
    );
  }

  @override
  List<Object?> get props => [person, isSaving, noticeMessage];
}

class AccountFailure extends AccountState {
  final String errorMessage;

  const AccountFailure({required this.errorMessage});

  @override
  List<Object?> get props => [errorMessage];
}
