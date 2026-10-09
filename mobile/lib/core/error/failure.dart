import 'package:equatable/equatable.dart';

abstract class Failure extends Equatable {
  final String message;
  final Exception? exception;

  const Failure({required this.message, this.exception});

  @override
  List<Object?> get props => [message, exception];
}

class NetworkFailure extends Failure {
  const NetworkFailure({required super.message, super.exception});
}

class StorageFailure extends Failure {
  const StorageFailure({required super.message, super.exception});
}

class UnknownFailure extends Failure {
  const UnknownFailure({required super.message, super.exception});
}
