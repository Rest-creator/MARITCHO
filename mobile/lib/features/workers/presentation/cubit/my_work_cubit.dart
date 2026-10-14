import 'dart:async';

import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/core/sync/outbox_item.dart';
import 'package:mobile/features/jobs/data/models/job.dart';
import 'package:mobile/features/jobs/data/repositories/job_work_repository.dart';
import 'package:mobile/features/workers/data/models/work_screen.dart';
import 'package:mobile/features/workers/data/repositories/work_screen_repository.dart';
import 'package:mobile/features/workers/presentation/cubit/my_work_state.dart';

/// W4 · My work: offers, active jobs (arrive + price, photos) and done jobs.
/// Work done on site is saved on the phone first and sent by the sync
/// service; [syncChanges] tells this screen when something went out.
class MyWorkCubit extends Cubit<MyWorkState> {
  final WorkScreenRepository _workScreenRepository;
  final JobWorkRepository _jobWorkRepository;
  StreamSubscription<void>? _syncSubscription;

  MyWorkCubit(
    this._workScreenRepository,
    this._jobWorkRepository, {
    required Stream<void> syncChanges,
  }) : super(MyWorkInitial()) {
    _syncSubscription = syncChanges.listen((void _) => unawaited(refresh()));
  }

  Future<void> load() async {
    emit(MyWorkLoading());
    final MyWorkState next = await _fetch();
    if (!isClosed) emit(next);
  }

  /// Re-read everything without a loading spinner (e.g. after a sync).
  Future<void> refresh() async {
    final MyWorkState current = state;
    final MyWorkState next = await _fetch();
    if (isClosed) return;
    if (next is MyWorkLoaded && current is MyWorkLoaded) {
      emit(next.copyWith(notice: current.notice));
    } else if (next is MyWorkLoaded || current is! MyWorkLoaded) {
      emit(next);
    }
  }

  /// "I've arrived": save the on-site price; returns false if it can't be.
  Future<bool> submitQuote({
    required String jobId,
    required double laborAmount,
    required double materialsAmount,
  }) async {
    final Result<void, Failure> result = await _jobWorkRepository.queueQuote(
      jobId: jobId,
      laborAmount: laborAmount,
      materialsAmount: materialsAmount,
    );
    return _afterQueue(
      result,
      "Price saved. It sends as soon as there's signal.",
    );
  }

  Future<bool> addPhoto({
    required String jobId,
    required String filePath,
  }) async {
    final Result<void, Failure> result = await _jobWorkRepository.queuePhoto(
      jobId: jobId,
      sourcePath: filePath,
    );
    return _afterQueue(
      result,
      "Photo saved. It goes to the client's chat when there's signal.",
    );
  }

  Future<void> retry(int itemId) async {
    final Result<void, Failure> result = await _jobWorkRepository.retry(itemId);
    await _afterQueue(result, 'Trying again.');
  }

  void clearNotice() {
    final MyWorkState current = state;
    if (current is MyWorkLoaded && current.notice != null) {
      emit(current.copyWith(clearNotice: true));
    }
  }

  Future<bool> _afterQueue(
    Result<void, Failure> result,
    String successNotice,
  ) async {
    final MyWorkState current = state;
    if (result.isError) {
      if (current is MyWorkLoaded && !isClosed) {
        emit(current.copyWith(notice: result.errorValue.message));
      }
      return false;
    }
    if (current is MyWorkLoaded && !isClosed) {
      final Map<String, List<OutboxItem>> undelivered = await _undeliveredFor(
        current.activeJobs,
      );
      if (!isClosed) {
        emit(current.copyWith(undelivered: undelivered, notice: successNotice));
      }
    }
    return true;
  }

  /// One request for the whole screen (ADR-009 phase 2).
  Future<MyWorkState> _fetch() async {
    final Result<WorkScreen, Failure> result = await _workScreenRepository
        .load();
    if (result.isError) return MyWorkFailure(result.errorValue.message);
    final WorkScreen screen = result.okValue;
    final MyWorkLoaded loaded = MyWorkLoaded(
      standing: screen.standing,
      offers: screen.offers,
      assignedJobs: screen.assigned,
    );
    return loaded.copyWith(
      undelivered: await _undeliveredFor(loaded.activeJobs),
    );
  }

  Future<Map<String, List<OutboxItem>>> _undeliveredFor(List<Job> jobs) async {
    final Map<String, List<OutboxItem>> byJob = <String, List<OutboxItem>>{};
    for (final Job job in jobs) {
      final Result<List<OutboxItem>, Failure> items = await _jobWorkRepository
          .undelivered(job.id);
      if (items.isOk && items.okValue.isNotEmpty) byJob[job.id] = items.okValue;
    }
    return byJob;
  }

  @override
  Future<void> close() async {
    await _syncSubscription?.cancel();
    return super.close();
  }
}
