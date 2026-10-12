import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/workers_repository.dart';
import 'worker_skills_state.dart';

class WorkerSkillsCubit extends Cubit<WorkerSkillsState> {
  final WorkersRepository _workersRepository;

  WorkerSkillsCubit(this._workersRepository) : super(WorkerSkillsInitial());

  Future<void> submit({
    required List<String> trades,
    required String suburb,
    String? travelMeans,
  }) async {
    emit(WorkerSkillsSubmitting());

    for (final trade in trades) {
      final result = await _workersRepository.registerSkill(trade: trade);
      if (result.isError) {
        emit(WorkerSkillsFailure(result.errorValue.message));
        return;
      }
    }

    final areaResult = await _workersRepository.registerServiceArea(
      suburb: suburb,
      travelMeans: travelMeans,
    );

    areaResult.fold(
      onOk: (_) => emit(WorkerSkillsSuccess()),
      onError: (failure) => emit(WorkerSkillsFailure(failure.message)),
    );
  }
}
