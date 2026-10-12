import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/jobs_repository.dart';
import 'job_tracking_state.dart';

class JobTrackingCubit extends Cubit<JobTrackingState> {
  final JobsRepository _jobsRepository;

  JobTrackingCubit(this._jobsRepository) : super(JobTrackingInitial());

  Future<void> completeJob({
    required String jobId,
    required String whatWasDone,
    String? clientWords,
  }) async {
    emit(JobTrackingSubmitting());

    final result = await _jobsRepository.completeJob(
      jobId: jobId,
      whatWasDone: whatWasDone,
      clientWords: clientWords,
    );

    result.fold(
      onOk: (job) => emit(JobTrackingSuccess(job)),
      onError: (failure) => emit(JobTrackingFailure(failure.message)),
    );
  }
}
