import 'package:equatable/equatable.dart';

import 'package:mobile/features/workers/data/models/worker_directory_item.dart';

abstract class WorkerProfileState extends Equatable {
  const WorkerProfileState();

  @override
  List<Object?> get props => [];
}

class WorkerProfileInitial extends WorkerProfileState {
  const WorkerProfileInitial();
}

class WorkerProfileLoading extends WorkerProfileState {
  const WorkerProfileLoading();
}

class WorkerProfileLoaded extends WorkerProfileState {
  final WorkerPublicProfile profile;

  const WorkerProfileLoaded({required this.profile});

  @override
  List<Object?> get props => [profile];
}

class WorkerProfileFailure extends WorkerProfileState {
  final String errorMessage;

  const WorkerProfileFailure({required this.errorMessage});

  @override
  List<Object?> get props => [errorMessage];
}
