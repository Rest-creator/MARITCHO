import 'package:equatable/equatable.dart';

import '../../data/models/person.dart';

abstract class AuthState extends Equatable {
  const AuthState();
  @override
  List<Object?> get props => [];
}

class AuthInitial extends AuthState {}

class AuthLoading extends AuthState {}

class AuthSuccess extends AuthState {
  final Person person;
  const AuthSuccess(this.person);
  @override
  List<Object?> get props => [person];
}

class AuthFailure extends AuthState {
  final String errorMessage;
  const AuthFailure(this.errorMessage);
  @override
  List<Object?> get props => [errorMessage];
}
