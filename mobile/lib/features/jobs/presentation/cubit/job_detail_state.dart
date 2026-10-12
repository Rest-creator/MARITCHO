import 'package:equatable/equatable.dart';

abstract class JobDetailState extends Equatable {
  const JobDetailState();
  @override
  List<Object?> get props => [];
}

class JobDetailInitial extends JobDetailState {}

class JobDetailSubmitting extends JobDetailState {}

class JobDetailSuccess extends JobDetailState {}

class JobDetailFailure extends JobDetailState {
  final String errorMessage;
  const JobDetailFailure(this.errorMessage);
  @override
  List<Object?> get props => [errorMessage];
}
