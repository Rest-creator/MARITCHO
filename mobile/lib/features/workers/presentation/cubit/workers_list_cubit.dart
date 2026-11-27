import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/features/workers/data/repositories/workers_repository.dart';
import 'package:mobile/features/workers/presentation/cubit/workers_list_state.dart';

class WorkersListCubit extends Cubit<WorkersListState> {
  final WorkersRepository _workersRepository;

  String? _currentTrade;
  String _currentQuery = '';

  WorkersListCubit(this._workersRepository) : super(const WorkersListInitial());

  Future<void> loadWorkers({String? trade, String? query}) async {
    _currentTrade = trade ?? _currentTrade;
    _currentQuery = query ?? _currentQuery;

    emit(const WorkersListLoading());
    final result = await _workersRepository.listNearbyWorkers(
      trade: _currentTrade,
      query: _currentQuery.isNotEmpty ? _currentQuery : null,
    );

    result.match(
      onOk: (workers) => emit(
        WorkersListLoaded(
          workers: workers,
          selectedTrade: _currentTrade,
          searchQuery: _currentQuery,
        ),
      ),
      onError: (failure) =>
          emit(WorkersListFailure(errorMessage: failure.message)),
    );
  }

  void filterTrade(String? trade) {
    _currentTrade = trade;
    loadWorkers();
  }

  void search(String query) {
    _currentQuery = query;
    loadWorkers();
  }
}
