import 'package:equatable/equatable.dart';

import '../../../jobs/data/models/job.dart';
import '../../../jobs/data/models/my_offer.dart';
import '../../data/models/standing.dart';

abstract class MyWorkState extends Equatable {
  const MyWorkState();
  @override
  List<Object?> get props => [];
}

class MyWorkInitial extends MyWorkState {}

class MyWorkLoading extends MyWorkState {}

class MyWorkLoaded extends MyWorkState {
  final Standing standing;
  final List<MyOffer> offers;
  final List<Job> assignedJobs;

  const MyWorkLoaded({
    required this.standing,
    required this.offers,
    required this.assignedJobs,
  });

  List<Job> get activeJobs =>
      assignedJobs.where((job) => job.status == 'BOOKED' || job.status == 'IN_PROGRESS').toList();

  List<Job> get doneJobs => assignedJobs.where((job) => job.status == 'COMPLETED').toList();

  @override
  List<Object?> get props => [standing, offers, assignedJobs];
}

class MyWorkFailure extends MyWorkState {
  final String errorMessage;
  const MyWorkFailure(this.errorMessage);
  @override
  List<Object?> get props => [errorMessage];
}
