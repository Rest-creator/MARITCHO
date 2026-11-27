import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/features/workers/data/repositories/workers_repository.dart';
import 'package:mobile/features/workers/presentation/cubit/worker_profile_state.dart';

class WorkerProfileCubit extends Cubit<WorkerProfileState> {
  final WorkersRepository workersRepository;
  final String workerId;

  WorkerProfileCubit({required this.workersRepository, required this.workerId})
    : super(const WorkerProfileInitial());

  Future<void> loadProfile({String? suburb}) async {
    emit(const WorkerProfileLoading());
    final result = await workersRepository.getWorkerProfile(
      workerId,
      suburb: suburb,
    );

    result.match(
      onOk: (profile) => emit(WorkerProfileLoaded(profile: profile)),
      onError: (failure) =>
          emit(WorkerProfileFailure(errorMessage: failure.message)),
    );
  }
}
