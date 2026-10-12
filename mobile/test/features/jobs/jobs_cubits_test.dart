import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/features/jobs/data/models/job.dart';
import 'package:mobile/features/jobs/data/models/match_candidate.dart';
import 'package:mobile/features/jobs/data/repositories/jobs_repository.dart';
import 'package:mobile/features/jobs/presentation/cubit/applicants_cubit.dart';
import 'package:mobile/features/jobs/presentation/cubit/applicants_state.dart';
import 'package:mobile/features/jobs/presentation/cubit/employer_home_cubit.dart';
import 'package:mobile/features/jobs/presentation/cubit/employer_home_state.dart';
import 'package:mobile/features/jobs/presentation/cubit/job_tracking_cubit.dart';
import 'package:mobile/features/jobs/presentation/cubit/job_tracking_state.dart';
import 'package:mobile/features/jobs/presentation/cubit/post_job_cubit.dart';
import 'package:mobile/features/jobs/presentation/cubit/post_job_state.dart';

Job _job({String status = 'REQUESTED', int? offerCount}) => Job(
  id: 'job-1',
  buyerId: 'buyer-1',
  workerId: null,
  status: status,
  trade: 'PLUMBING',
  suburb: 'Nkulumane',
  address: '12 Fife Street',
  problemDescription: 'Leaking tap',
  budgetAmount: null,
  currency: null,
  quoteAmount: null,
  createdAt: DateTime(2026, 1, 1),
  offerCount: offerCount,
);

const _candidate = MatchCandidate(
  workerId: 'worker-1',
  suburb: 'Nkulumane',
  distanceBand: 'SAME_SUBURB',
  distanceKm: 0,
  grade: 'REGISTERED',
  onTimeRate: 100,
  jobsCompleted: 0,
  reason: 'PLUMBING skill nearby',
  quotedAmount: 30,
  availabilityNote: null,
);

class _FakeJobsRepository extends JobsRepository {
  final Result<List<Job>, Failure> listMineResult;
  final Result<Job, Failure> createJobResult;
  final Result<List<MatchCandidate>, Failure> getMatchesResult;
  final Result<Job, Failure> bookJobResult;
  final Result<Job, Failure> completeJobResult;

  static final _defaultCreatedAt = DateTime(2026, 1, 1);

  _FakeJobsRepository({
    this.listMineResult = const Ok([]),
    Result<Job, Failure>? createJobResult,
    this.getMatchesResult = const Ok([]),
    Result<Job, Failure>? bookJobResult,
    Result<Job, Failure>? completeJobResult,
  }) : createJobResult = createJobResult ??
            Ok(Job(
              id: 'job-1', buyerId: 'b', workerId: null, status: 'REQUESTED', trade: 'PLUMBING',
              suburb: 'Nkulumane', address: 'x', problemDescription: null, budgetAmount: null,
              currency: null, quoteAmount: null, createdAt: _defaultCreatedAt,
            )),
       bookJobResult = bookJobResult ??
            Ok(Job(
              id: 'job-1', buyerId: 'b', workerId: 'w', status: 'BOOKED', trade: 'PLUMBING',
              suburb: 'Nkulumane', address: 'x', problemDescription: null, budgetAmount: null,
              currency: null, quoteAmount: null, createdAt: _defaultCreatedAt,
            )),
       completeJobResult = completeJobResult ??
            Ok(Job(
              id: 'job-1', buyerId: 'b', workerId: 'w', status: 'COMPLETED', trade: 'PLUMBING',
              suburb: 'Nkulumane', address: 'x', problemDescription: null, budgetAmount: null,
              currency: null, quoteAmount: null, createdAt: _defaultCreatedAt,
            )),
       super(Dio());

  @override
  Future<Result<List<Job>, Failure>> listMine() async => listMineResult;

  @override
  Future<Result<Job, Failure>> createJob({
    required String trade,
    required String suburb,
    required String address,
    required String problemDescription,
    double? budgetAmount,
  }) async => createJobResult;

  @override
  Future<Result<List<MatchCandidate>, Failure>> getMatches(String jobId) async => getMatchesResult;

  @override
  Future<Result<Job, Failure>> bookJob({
    required String jobId,
    required String workerId,
    required double depositAmount,
    String currency = 'USD',
  }) async => bookJobResult;

  @override
  Future<Result<Job, Failure>> completeJob({
    required String jobId,
    required String whatWasDone,
    String? clientWords,
  }) async => completeJobResult;
}

void main() {
  group('EmployerHomeCubit', () {
    test('loads jobs into EmployerHomeLoaded', () async {
      final cubit = EmployerHomeCubit(
        _FakeJobsRepository(listMineResult: Ok([_job(offerCount: 2)])),
      );

      await cubit.loadJobs();

      expect(cubit.state, isA<EmployerHomeLoaded>());
      expect((cubit.state as EmployerHomeLoaded).jobs.single.offerCount, 2);
      await cubit.close();
    });

    test('emits EmployerHomeFailure on error', () async {
      final cubit = EmployerHomeCubit(
        _FakeJobsRepository(listMineResult: const Error(NetworkFailure(message: 'down'))),
      );

      await cubit.loadJobs();

      expect(cubit.state, isA<EmployerHomeFailure>());
      await cubit.close();
    });
  });

  group('PostJobCubit', () {
    test('ends in PostJobSuccess on success', () async {
      final cubit = PostJobCubit(_FakeJobsRepository());

      await cubit.submit(
        trade: 'PLUMBING',
        suburb: 'Nkulumane',
        address: '12 Fife Street',
        problemDescription: 'Leaking tap',
      );

      expect(cubit.state, isA<PostJobSuccess>());
      await cubit.close();
    });
  });

  group('ApplicantsCubit', () {
    test('loads candidates then books successfully', () async {
      final cubit = ApplicantsCubit(
        _FakeJobsRepository(getMatchesResult: const Ok([_candidate])),
      );

      await cubit.loadMatches('job-1');
      expect(cubit.state, isA<ApplicantsLoaded>());

      await cubit.hireWorker(jobId: 'job-1', workerId: 'worker-1', depositAmount: 30);
      expect(cubit.state, isA<ApplicantsBooked>());
      await cubit.close();
    });
  });

  group('JobTrackingCubit', () {
    test('ends in JobTrackingSuccess on completion', () async {
      final cubit = JobTrackingCubit(_FakeJobsRepository());

      await cubit.completeJob(jobId: 'job-1', whatWasDone: 'Fixed the tap');

      expect(cubit.state, isA<JobTrackingSuccess>());
      await cubit.close();
    });
  });
}
