import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/jobs_repository.dart';
import 'employer_home_state.dart';

class EmployerHomeCubit extends Cubit<EmployerHomeState> {
  final JobsRepository _jobsRepository;

  EmployerHomeCubit(this._jobsRepository) : super(EmployerHomeInitial());

  Future<void> loadJobs() async {
    emit(EmployerHomeLoading());

    final result = await _jobsRepository.listMine();

    result.fold(
      onOk: (jobs) => emit(EmployerHomeLoaded(jobs)),
      onError: (failure) => emit(EmployerHomeFailure(failure.message)),
    );
  }
}
