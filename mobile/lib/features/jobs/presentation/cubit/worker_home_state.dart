import 'package:equatable/equatable.dart';

import '../../data/models/open_job.dart';

abstract class WorkerHomeState extends Equatable {
  const WorkerHomeState();
  @override
  List<Object?> get props => [];
}

class WorkerHomeInitial extends WorkerHomeState {}

class WorkerHomeLoading extends WorkerHomeState {}

class WorkerHomeLoaded extends WorkerHomeState {
  final List<OpenJob> jobs;
  const WorkerHomeLoaded(this.jobs);
  @override
  List<Object?> get props => [jobs];
}

class WorkerHomeFailure extends WorkerHomeState {
  final String errorMessage;
  const WorkerHomeFailure(this.errorMessage);
  @override
  List<Object?> get props => [errorMessage];
}
