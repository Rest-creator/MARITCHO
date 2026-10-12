import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/jobs_repository.dart';
import 'applicants_state.dart';

class ApplicantsCubit extends Cubit<ApplicantsState> {
  final JobsRepository _jobsRepository;

  ApplicantsCubit(this._jobsRepository) : super(ApplicantsInitial());

  Future<void> loadMatches(String jobId) async {
    emit(ApplicantsLoading());

    final result = await _jobsRepository.getMatches(jobId);

    result.fold(
      onOk: (candidates) => emit(ApplicantsLoaded(candidates)),
      onError: (failure) => emit(ApplicantsFailure(failure.message)),
    );
  }

  Future<void> hireWorker({
    required String jobId,
    required String workerId,
    required double depositAmount,
  }) async {
    final current = state;
    if (current is ApplicantsLoaded) {
      emit(ApplicantsBooking(current.candidates));
    }

    final result = await _jobsRepository.bookJob(
      jobId: jobId,
      workerId: workerId,
      depositAmount: depositAmount,
    );

    result.fold(
      onOk: (job) => emit(ApplicantsBooked(job)),
      onError: (failure) => emit(ApplicantsFailure(failure.message)),
    );
  }
}
