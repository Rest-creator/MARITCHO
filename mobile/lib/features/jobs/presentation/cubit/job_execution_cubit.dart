import 'package:flutter_bloc/flutter_bloc.dart';
import '../../data/repositories/check_in_repository.dart';
import '../../data/repositories/photo_repository.dart';
import 'job_execution_state.dart';

class JobExecutionCubit extends Cubit<JobExecutionState> {
  final CheckInRepository _checkInRepository;
  final PhotoRepository _photoRepository;

  JobExecutionCubit(this._checkInRepository, this._photoRepository) 
      : super(JobExecutionInitial());

  Future<void> submitCheckIn({
    required String jobId,
    required String workerId,
    double? latitude,
    double? longitude,
  }) async {
    emit(JobExecutionLoading());
    
    final result = await _checkInRepository.recordCheckIn(
      jobId: jobId,
      workerId: workerId,
      latitude: latitude,
      longitude: longitude,
    );

    result.fold(
      onOk: (_) => emit(const JobExecutionSuccess('Check-in recorded offline. Will sync when connected.')),
      onError: (failure) => emit(JobExecutionFailure(failure.message)),
    );
  }

  Future<void> submitPhoto({
    required String jobId,
    required String filePath,
    required String photoType,
  }) async {
    emit(JobExecutionLoading());
    
    final result = await _photoRepository.queuePhotoUpload(
      jobId: jobId,
      filePath: filePath,
      photoType: photoType,
    );

    result.fold(
      onOk: (_) => emit(const JobExecutionSuccess('Photo queued for upload.')),
      onError: (failure) => emit(JobExecutionFailure(failure.message)),
    );
  }
}
