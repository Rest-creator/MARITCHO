import 'package:equatable/equatable.dart';

abstract class JobExecutionState extends Equatable {
  const JobExecutionState();

  @override
  List<Object?> get props => [];
}

class JobExecutionInitial extends JobExecutionState {}

class JobExecutionLoading extends JobExecutionState {}

class JobExecutionSuccess extends JobExecutionState {
  final String message;

  const JobExecutionSuccess(this.message);

  @override
  List<Object?> get props => [message];
}

class JobExecutionFailure extends JobExecutionState {
  final String errorMessage;

  const JobExecutionFailure(this.errorMessage);

  @override
  List<Object?> get props => [errorMessage];
}
