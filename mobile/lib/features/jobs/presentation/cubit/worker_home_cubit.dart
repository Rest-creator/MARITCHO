import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/jobs_repository.dart';
import 'worker_home_state.dart';

class WorkerHomeCubit extends Cubit<WorkerHomeState> {
  final JobsRepository _jobsRepository;

  WorkerHomeCubit(this._jobsRepository) : super(WorkerHomeInitial());

  Future<void> loadOpenJobs() async {
    emit(WorkerHomeLoading());

    final result = await _jobsRepository.listOpen();

    result.fold(
      onOk: (jobs) => emit(WorkerHomeLoaded(jobs)),
      onError: (failure) => emit(WorkerHomeFailure(failure.message)),
    );
  }
}
