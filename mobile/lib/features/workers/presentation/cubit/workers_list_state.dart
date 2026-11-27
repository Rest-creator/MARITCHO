import 'package:equatable/equatable.dart';

import 'package:mobile/features/workers/data/models/worker_directory_item.dart';

abstract class WorkersListState extends Equatable {
  const WorkersListState();

  @override
  List<Object?> get props => [];
}

class WorkersListInitial extends WorkersListState {
  const WorkersListInitial();
}

class WorkersListLoading extends WorkersListState {
  const WorkersListLoading();
}

class WorkersListLoaded extends WorkersListState {
  final List<WorkerDirectoryItem> workers;
  final String? selectedTrade;
  final String searchQuery;

  const WorkersListLoaded({
    required this.workers,
    this.selectedTrade,
    this.searchQuery = '',
  });

  WorkersListLoaded copyWith({
    List<WorkerDirectoryItem>? workers,
    String? selectedTrade,
    String? searchQuery,
    bool clearTrade = false,
  }) {
    return WorkersListLoaded(
      workers: workers ?? this.workers,
      selectedTrade: clearTrade ? null : (selectedTrade ?? this.selectedTrade),
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }

  @override
  List<Object?> get props => [workers, selectedTrade, searchQuery];
}

class WorkersListFailure extends WorkersListState {
  final String errorMessage;

  const WorkersListFailure({required this.errorMessage});

  @override
  List<Object?> get props => [errorMessage];
}
