import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/jobs_repository.dart';
import 'post_job_state.dart';

class PostJobCubit extends Cubit<PostJobState> {
  final JobsRepository _jobsRepository;

  PostJobCubit(this._jobsRepository) : super(PostJobInitial());

  Future<void> submit({
    required String trade,
    required String suburb,
    required String address,
    required String problemDescription,
    double? budgetAmount,
  }) async {
    emit(PostJobSubmitting());

    final result = await _jobsRepository.createJob(
      trade: trade,
      suburb: suburb,
      address: address,
      problemDescription: problemDescription,
      budgetAmount: budgetAmount,
    );

    result.fold(
      onOk: (job) => emit(PostJobSuccess(job)),
      onError: (failure) => emit(PostJobFailure(failure.message)),
    );
  }
}
