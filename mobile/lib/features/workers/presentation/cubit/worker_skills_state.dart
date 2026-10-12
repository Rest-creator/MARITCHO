import 'package:equatable/equatable.dart';

abstract class WorkerSkillsState extends Equatable {
  const WorkerSkillsState();
  @override
  List<Object?> get props => [];
}

class WorkerSkillsInitial extends WorkerSkillsState {}

class WorkerSkillsSubmitting extends WorkerSkillsState {}

class WorkerSkillsSuccess extends WorkerSkillsState {}

class WorkerSkillsFailure extends WorkerSkillsState {
  final String errorMessage;
  const WorkerSkillsFailure(this.errorMessage);
  @override
  List<Object?> get props => [errorMessage];
}
