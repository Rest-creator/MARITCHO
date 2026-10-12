import 'package:equatable/equatable.dart';

import '../../data/models/job.dart';

abstract class PostJobState extends Equatable {
  const PostJobState();
  @override
  List<Object?> get props => [];
}

class PostJobInitial extends PostJobState {}

class PostJobSubmitting extends PostJobState {}

class PostJobSuccess extends PostJobState {
  final Job job;
  const PostJobSuccess(this.job);
  @override
  List<Object?> get props => [job];
}

class PostJobFailure extends PostJobState {
  final String errorMessage;
  const PostJobFailure(this.errorMessage);
  @override
  List<Object?> get props => [errorMessage];
}
