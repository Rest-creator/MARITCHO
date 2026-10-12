import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/features/jobs/data/models/job.dart';
import 'package:mobile/features/jobs/data/models/match_candidate.dart';
import 'package:mobile/features/jobs/data/models/my_offer.dart';
import 'package:mobile/features/jobs/data/models/open_job.dart';
import 'package:mobile/features/jobs/data/repositories/jobs_repository.dart';
import 'package:mobile/features/jobs/presentation/cubit/job_detail_cubit.dart';
import 'package:mobile/features/jobs/presentation/cubit/job_detail_state.dart';
import 'package:mobile/features/jobs/presentation/cubit/worker_home_cubit.dart';
import 'package:mobile/features/jobs/presentation/cubit/worker_home_state.dart';
import 'package:mobile/features/workers/data/models/standing.dart';
import 'package:mobile/features/workers/data/repositories/workers_repository.dart';
import 'package:mobile/features/workers/presentation/cubit/my_work_cubit.dart';
import 'package:mobile/features/workers/presentation/cubit/my_work_state.dart';
import 'package:mobile/features/workers/presentation/cubit/worker_skills_cubit.dart';
import 'package:mobile/features/workers/presentation/cubit/worker_skills_state.dart';
import 'package:mobile/core/storage/database_helper.dart';

const _openJob = OpenJob(
  jobId: 'job-1',
  trade: 'PLUMBING',
  suburb: 'Nkulumane',
  budgetAmount: 40,
  problemDescription: 'Leaking tap',
  distanceBand: 'SAME_SUBURB',
  distanceKm: 0,
);

class _FakeWorkersRepository extends WorkersRepository {
  final Result<void, Failure> registerSkillResult;
  final Result<void, Failure> registerServiceAreaResult;
  final Result<Standing, Failure> standingResult;

  _FakeWorkersRepository({
    this.registerSkillResult = const Ok(null),
    this.registerServiceAreaResult = const Ok(null),
    this.standingResult = const Ok(
      Standing(
        grade: 'REGISTERED',
        onTimeRate: 100,
        disputeRate: 0,
        fillRate: 0,
        jobsCompleted: 0,
        isFrozen: false,
      ),
    ),
  }) : super(Dio(), DatabaseHelper());

  @override
  Future<Result<void, Failure>> registerSkill({
    required String trade,
    String? proofUrl,
  }) async => registerSkillResult;

  @override
  Future<Result<void, Failure>> registerServiceArea({
    required String suburb,
    String? travelMeans,
  }) async => registerServiceAreaResult;

  @override
  Future<Result<Standing, Failure>> getStanding() async => standingResult;
}

class _FakeJobsRepository extends JobsRepository {
  final Result<List<OpenJob>, Failure> listOpenResult;
  final Result<void, Failure> submitOfferResult;
  final Result<List<Job>, Failure> listAssignedResult;
  final Result<List<MyOffer>, Failure> listMyOffersResult;

  _FakeJobsRepository({
    this.listOpenResult = const Ok([_openJob]),
    this.submitOfferResult = const Ok(null),
    this.listAssignedResult = const Ok([]),
    this.listMyOffersResult = const Ok([]),
  }) : super(Dio(), DatabaseHelper());

  @override
  Future<Result<List<OpenJob>, Failure>> listOpen() async => listOpenResult;

  @override
  Future<Result<void, Failure>> submitOffer({
    required String jobId,
    required double quotedAmount,
    String? availabilityNote,
  }) async => submitOfferResult;

  @override
  Future<Result<List<Job>, Failure>> listAssigned() async => listAssignedResult;

  @override
  Future<Result<List<MyOffer>, Failure>> listMyOffers() async => listMyOffersResult;

  @override
  Future<Result<List<MatchCandidate>, Failure>> getMatches(String jobId) async => const Ok([]);
}

void main() {
  group('WorkerSkillsCubit', () {
    test('ends in WorkerSkillsSuccess when both calls succeed', () async {
      final cubit = WorkerSkillsCubit(_FakeWorkersRepository());

      await cubit.submit(trades: ['PLUMBING'], suburb: 'Nkulumane');

      expect(cubit.state, isA<WorkerSkillsSuccess>());
      await cubit.close();
    });

    test('ends in WorkerSkillsFailure when a skill registration fails', () async {
      final cubit = WorkerSkillsCubit(
        _FakeWorkersRepository(
          registerSkillResult: const Error(NetworkFailure(message: 'nope')),
        ),
      );

      await cubit.submit(trades: ['PLUMBING'], suburb: 'Nkulumane');

      expect(cubit.state, isA<WorkerSkillsFailure>());
      await cubit.close();
    });
  });

  group('WorkerHomeCubit', () {
    test('loads open jobs into WorkerHomeLoaded', () async {
      final cubit = WorkerHomeCubit(_FakeJobsRepository());

      await cubit.loadOpenJobs();

      expect(cubit.state, isA<WorkerHomeLoaded>());
      expect((cubit.state as WorkerHomeLoaded).jobs.single.jobId, 'job-1');
      await cubit.close();
    });
  });

  group('JobDetailCubit', () {
    test('ends in JobDetailSuccess when the offer submits', () async {
      final cubit = JobDetailCubit(_FakeJobsRepository());

      await cubit.submitOffer(jobId: 'job-1', quotedAmount: 35);

      expect(cubit.state, isA<JobDetailSuccess>());
      await cubit.close();
    });
  });

  group('MyWorkCubit', () {
    test('loads standing, offers and assigned jobs into MyWorkLoaded', () async {
      final cubit = MyWorkCubit(_FakeWorkersRepository(), _FakeJobsRepository());

      await cubit.load();

      expect(cubit.state, isA<MyWorkLoaded>());
      final loaded = cubit.state as MyWorkLoaded;
      expect(loaded.standing.jobsCompleted, 0);
      await cubit.close();
    });

    test('ends in MyWorkFailure when the standing fetch fails', () async {
      final cubit = MyWorkCubit(
        _FakeWorkersRepository(
          standingResult: const Error(NetworkFailure(message: 'down')),
        ),
        _FakeJobsRepository(),
      );

      await cubit.load();

      expect(cubit.state, isA<MyWorkFailure>());
      await cubit.close();
    });
  });
}
