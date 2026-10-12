import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/jobs_repository.dart';
import 'job_detail_state.dart';

class JobDetailCubit extends Cubit<JobDetailState> {
  final JobsRepository _jobsRepository;

  JobDetailCubit(this._jobsRepository) : super(JobDetailInitial());

  Future<void> submitOffer({
    required String jobId,
    required double quotedAmount,
    String? availabilityNote,
  }) async {
    emit(JobDetailSubmitting());

    final result = await _jobsRepository.submitOffer(
      jobId: jobId,
      quotedAmount: quotedAmount,
      availabilityNote: availabilityNote,
    );

    result.fold(
      onOk: (_) => emit(JobDetailSuccess()),
      onError: (failure) => emit(JobDetailFailure(failure.message)),
    );
  }
}
