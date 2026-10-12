import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../jobs/data/repositories/jobs_repository.dart';
import '../../data/repositories/workers_repository.dart';
import 'my_work_state.dart';

class MyWorkCubit extends Cubit<MyWorkState> {
  final WorkersRepository _workersRepository;
  final JobsRepository _jobsRepository;

  MyWorkCubit(this._workersRepository, this._jobsRepository) : super(MyWorkInitial());

  Future<void> load() async {
    emit(MyWorkLoading());

    final standingResult = await _workersRepository.getStanding();
    if (standingResult.isError) {
      emit(MyWorkFailure(standingResult.errorValue.message));
      return;
    }

    final offersResult = await _jobsRepository.listMyOffers();
    if (offersResult.isError) {
      emit(MyWorkFailure(offersResult.errorValue.message));
      return;
    }

    final assignedResult = await _jobsRepository.listAssigned();
    if (assignedResult.isError) {
      emit(MyWorkFailure(assignedResult.errorValue.message));
      return;
    }

    emit(
      MyWorkLoaded(
        standing: standingResult.okValue,
        offers: offersResult.okValue,
        assignedJobs: assignedResult.okValue,
      ),
    );
  }
}
