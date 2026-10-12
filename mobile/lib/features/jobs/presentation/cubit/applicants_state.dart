import 'package:equatable/equatable.dart';

import '../../data/models/job.dart';
import '../../data/models/match_candidate.dart';

abstract class ApplicantsState extends Equatable {
  const ApplicantsState();
  @override
  List<Object?> get props => [];
}

class ApplicantsInitial extends ApplicantsState {}

class ApplicantsLoading extends ApplicantsState {}

class ApplicantsLoaded extends ApplicantsState {
  final List<MatchCandidate> candidates;
  const ApplicantsLoaded(this.candidates);
  @override
  List<Object?> get props => [candidates];
}

/// Candidates stay visible while a hire is in flight, so the list doesn't
/// disappear behind a bare spinner.
class ApplicantsBooking extends ApplicantsState {
  final List<MatchCandidate> candidates;
  const ApplicantsBooking(this.candidates);
  @override
  List<Object?> get props => [candidates];
}

class ApplicantsBooked extends ApplicantsState {
  final Job job;
  const ApplicantsBooked(this.job);
  @override
  List<Object?> get props => [job];
}

class ApplicantsFailure extends ApplicantsState {
  final String errorMessage;
  const ApplicantsFailure(this.errorMessage);
  @override
  List<Object?> get props => [errorMessage];
}
