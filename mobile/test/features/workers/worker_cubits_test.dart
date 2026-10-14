import 'dart:async';

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
import 'package:mobile/features/workers/data/models/work_screen.dart';
import 'package:mobile/features/workers/data/repositories/work_screen_repository.dart';
import 'package:mobile/features/workers/data/repositories/workers_repository.dart';
import 'package:mobile/features/workers/presentation/cubit/my_work_cubit.dart';
import 'package:mobile/features/workers/presentation/cubit/my_work_state.dart';
import 'package:mobile/features/workers/presentation/cubit/worker_skills_cubit.dart';
import 'package:mobile/features/workers/presentation/cubit/worker_skills_state.dart';
import 'package:mobile/core/storage/database_helper.dart';
import 'package:mobile/core/sync/outbox_actions.dart';
import 'package:mobile/core/sync/outbox_item.dart';
import 'package:mobile/features/jobs/data/repositories/job_work_repository.dart';

import '../../support/fake_outbox.dart';

JobWorkRepository _workRepository() => JobWorkRepository(
  FakeOutbox(),
  onQueued: () {},
  photoDirectory: () async => throw UnimplementedError(),
);

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
  final Result<void, Failure> registerServiceAreaResult = const Ok(null);

  _FakeWorkersRepository({this.registerSkillResult = const Ok(null)})
    : super(Dio(), DatabaseHelper());

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
}

class _FakeJobsRepository extends JobsRepository {
  final Result<List<OpenJob>, Failure> listOpenResult = const Ok([_openJob]);
  final Result<void, Failure> submitOfferResult = const Ok(null);

  _FakeJobsRepository() : super(Dio(), DatabaseHelper());

  @override
  Future<Result<List<OpenJob>, Failure>> listOpen() async => listOpenResult;

  @override
  Future<Result<void, Failure>> submitOffer({
    required String jobId,
    required double quotedAmount,
    String? availabilityNote,
  }) async => submitOfferResult;

  @override
  Future<Result<List<MatchCandidate>, Failure>> getMatches(
    String jobId,
  ) async => const Ok([]);
}

const Standing _standing = Standing(
  grade: 'REGISTERED',
  onTimeRate: 100,
  disputeRate: 0,
  fillRate: 0,
  jobsCompleted: 0,
  isFrozen: false,
);

/// "My work" comes from one BFF request now (ADR-009 phase 2).
class _FakeWorkScreenRepository extends WorkScreenRepository {
  final Result<WorkScreen, Failure> result;

  _FakeWorkScreenRepository({
    this.result = const Ok(
      WorkScreen(standing: _standing, offers: <MyOffer>[], assigned: <Job>[]),
    ),
  }) : super(Dio(), DatabaseHelper());

  @override
  Future<Result<WorkScreen, Failure>> load() async => result;
}

void main() {
  group('WorkerSkillsCubit', () {
    test('ends in WorkerSkillsSuccess when both calls succeed', () async {
      final cubit = WorkerSkillsCubit(_FakeWorkersRepository());

      await cubit.submit(trades: ['PLUMBING'], suburb: 'Nkulumane');

      expect(cubit.state, isA<WorkerSkillsSuccess>());
      await cubit.close();
    });

    test(
      'ends in WorkerSkillsFailure when a skill registration fails',
      () async {
        final cubit = WorkerSkillsCubit(
          _FakeWorkersRepository(
            registerSkillResult: const Error(NetworkFailure(message: 'nope')),
          ),
        );

        await cubit.submit(trades: ['PLUMBING'], suburb: 'Nkulumane');

        expect(cubit.state, isA<WorkerSkillsFailure>());
        await cubit.close();
      },
    );
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
    test(
      'loads standing, offers and assigned jobs into MyWorkLoaded',
      () async {
        final cubit = MyWorkCubit(
          _FakeWorkScreenRepository(),
          _workRepository(),
          syncChanges: const Stream<void>.empty(),
        );

        await cubit.load();

        expect(cubit.state, isA<MyWorkLoaded>());
        final loaded = cubit.state as MyWorkLoaded;
        expect(loaded.standing.jobsCompleted, 0);
        await cubit.close();
      },
    );

    test('ends in MyWorkFailure when the screen fails to load', () async {
      final cubit = MyWorkCubit(
        _FakeWorkScreenRepository(
          result: const Error(NetworkFailure(message: 'down')),
        ),
        _workRepository(),
        syncChanges: const Stream<void>.empty(),
      );

      await cubit.load();

      expect(cubit.state, isA<MyWorkFailure>());
      await cubit.close();
    });
  });

  group('MyWorkCubit on site (APP-002)', () {
    final Job bookedJob = Job(
      id: 'job-9',
      buyerId: 'buyer-1',
      workerId: 'worker-1',
      status: 'BOOKED',
      trade: 'PLUMBING',
      suburb: 'Hillside',
      address: '14 Harrow Rd',
      problemDescription: 'Leaking tap',
      budgetAmount: 40,
      currency: 'USD',
      quoteAmount: null,
      createdAt: DateTime.utc(2026, 10, 14),
    );
    const MyOffer offer = MyOffer(
      id: 'offer-9',
      jobId: 'job-9',
      quotedAmount: 35,
      availabilityNote: null,
      jobTrade: 'PLUMBING',
      jobSuburb: 'Hillside',
      jobStatus: 'BOOKED',
    );

    MyWorkCubit cubitWith(FakeOutbox outbox, StreamController<void> sync) =>
        MyWorkCubit(
          _FakeWorkScreenRepository(
            result: Ok(
              WorkScreen(
                standing: _standing,
                offers: const <MyOffer>[offer],
                assigned: <Job>[bookedJob],
              ),
            ),
          ),
          JobWorkRepository(
            outbox,
            onQueued: () {},
            photoDirectory: () async => throw UnimplementedError(),
          ),
          syncChanges: sync.stream,
        );

    test(
      'pre-fills the price from the offer and shows a queued price',
      () async {
        final FakeOutbox outbox = FakeOutbox();
        final StreamController<void> sync = StreamController<void>.broadcast();
        final MyWorkCubit cubit = cubitWith(outbox, sync);
        await cubit.load();

        final MyWorkLoaded loaded = cubit.state as MyWorkLoaded;
        expect(loaded.activeJobs.single.id, 'job-9');
        expect(loaded.offeredAmountFor('job-9'), 35);

        final bool saved = await cubit.submitQuote(
          jobId: 'job-9',
          laborAmount: 35,
          materialsAmount: 5,
        );

        expect(saved, isTrue);
        final MyWorkLoaded after = cubit.state as MyWorkLoaded;
        expect(
          after.undeliveredFor('job-9').single.type,
          OutboxActions.submitQuote,
        );
        expect(after.notice, contains('Price saved'));
        await cubit.close();
        await sync.close();
      },
    );

    test('a refused price shows why and can be tried again', () async {
      final FakeOutbox outbox = FakeOutbox();
      final StreamController<void> sync = StreamController<void>.broadcast();
      final MyWorkCubit cubit = cubitWith(outbox, sync);
      await cubit.load();
      await cubit.submitQuote(
        jobId: 'job-9',
        laborAmount: 2,
        materialsAmount: 0,
      );
      final int id = outbox.items.keys.single;
      await outbox.markFailed(id, error: 'Quote must exceed deposit');

      sync.add(null); // what SyncService does after a pass
      await Future<void>.delayed(Duration.zero);
      await Future<void>.delayed(Duration.zero);

      final OutboxItem refused = (cubit.state as MyWorkLoaded)
          .undeliveredFor('job-9')
          .single;
      expect(refused.status, OutboxStatus.failed);
      expect(refused.lastError, 'Quote must exceed deposit');

      await cubit.retry(id);
      expect(outbox.items[id]!.status, OutboxStatus.pending);
      await cubit.close();
      await sync.close();
    });

    test(
      'a price of nothing is refused with a message, nothing queued',
      () async {
        final FakeOutbox outbox = FakeOutbox();
        final StreamController<void> sync = StreamController<void>.broadcast();
        final MyWorkCubit cubit = cubitWith(outbox, sync);
        await cubit.load();

        final bool saved = await cubit.submitQuote(
          jobId: 'job-9',
          laborAmount: 0,
          materialsAmount: 0,
        );

        expect(saved, isFalse);
        expect(
          (cubit.state as MyWorkLoaded).notice,
          'Enter what your work costs.',
        );
        expect(outbox.items, isEmpty);
        await cubit.close();
        await sync.close();
      },
    );
  });
}
