import 'package:equatable/equatable.dart';

import '../../data/models/job.dart';

abstract class JobTrackingState extends Equatable {
  const JobTrackingState();
  @override
  List<Object?> get props => [];
}

class JobTrackingInitial extends JobTrackingState {}

class JobTrackingSubmitting extends JobTrackingState {}

class JobTrackingSuccess extends JobTrackingState {
  final Job job;
  const JobTrackingSuccess(this.job);
  @override
  List<Object?> get props => [job];
}

class JobTrackingFailure extends JobTrackingState {
  final String errorMessage;
  const JobTrackingFailure(this.errorMessage);
  @override
  List<Object?> get props => [errorMessage];
}
