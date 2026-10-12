import 'package:equatable/equatable.dart';

import '../../data/models/job.dart';

abstract class EmployerHomeState extends Equatable {
  const EmployerHomeState();
  @override
  List<Object?> get props => [];
}

class EmployerHomeInitial extends EmployerHomeState {}

class EmployerHomeLoading extends EmployerHomeState {}

class EmployerHomeLoaded extends EmployerHomeState {
  final List<Job> jobs;
  const EmployerHomeLoaded(this.jobs);
  @override
  List<Object?> get props => [jobs];
}

class EmployerHomeFailure extends EmployerHomeState {
  final String errorMessage;
  const EmployerHomeFailure(this.errorMessage);
  @override
  List<Object?> get props => [errorMessage];
}
