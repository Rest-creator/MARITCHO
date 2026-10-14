import 'package:equatable/equatable.dart';

import 'package:mobile/features/accounts/data/models/person.dart';

abstract class AuthState extends Equatable {
  const AuthState();
  @override
  List<Object?> get props => <Object?>[];
}

class AuthInitial extends AuthState {}

class AuthLoading extends AuthState {}

/// A code was sent to [phone]; waiting for the person to type it in.
class AuthCodeRequired extends AuthState {
  final String phone;
  final bool isVerifying;

  /// Why the last code or resend didn't work, if it didn't.
  final String? errorMessage;

  const AuthCodeRequired({
    required this.phone,
    this.isVerifying = false,
    this.errorMessage,
  });

  @override
  List<Object?> get props => <Object?>[phone, isVerifying, errorMessage];
}

class AuthSuccess extends AuthState {
  final Person person;
  const AuthSuccess(this.person);
  @override
  List<Object?> get props => <Object?>[person];
}

class AuthFailure extends AuthState {
  final String errorMessage;
  const AuthFailure(this.errorMessage);
  @override
  List<Object?> get props => <Object?>[errorMessage];
}
