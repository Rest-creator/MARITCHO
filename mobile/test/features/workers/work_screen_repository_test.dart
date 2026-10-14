import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/core/storage/database_helper.dart';
import 'package:mobile/features/workers/data/models/work_screen.dart';
import 'package:mobile/features/workers/data/repositories/work_screen_repository.dart';

import '../../support/fake_http_adapter.dart';

/// Stands in for the SQLite response cache.
class _MemoryCache extends Fake implements DatabaseHelper {
  final Map<String, String> entries = <String, String>{};

  @override
  Future<void> cacheResponse(String cacheKey, String payload) async =>
      entries[cacheKey] = payload;

  @override
  Future<String?> getCachedResponse(String cacheKey) async => entries[cacheKey];
}

const Map<String, Object?> _bundle = <String, Object?>{
  'standing': <String, Object?>{
    'worker_id': 'w1',
    'grade': 'JOURNEYMAN',
    'on_time_rate': '92.00',
    'dispute_rate': '3.00',
    'fill_rate': '85.00',
    'jobs_completed': 14,
    'is_frozen': false,
  },
  'offers': <Object?>[
    <String, Object?>{
      'id': 'o1',
      'job_id': 'job-1',
      'quoted_amount': '25.00',
      'availability_note': null,
      'job_trade': 'ELECTRICAL',
      'job_suburb': 'Kumalo',
      'job_status': 'MATCHED',
    },
  ],
  'assigned': <Object?>[
    <String, Object?>{
      'id': 'job-2',
      'buyer_id': 'b1',
      'worker_id': 'w1',
      'status': 'BOOKED',
      'trade': 'PLUMBING',
      'suburb': 'Njube',
      'address': '22 Lobengula St',
      'problem_description': 'Geyser dripping',
      'budget_amount': '60.00',
      'currency': 'USD',
      'quote_amount': null,
      'created_at': '2026-10-14T06:00:00Z',
    },
  ],
};

void main() {
  test('loads the whole screen in one request and keeps a copy', () async {
    final FakeHttpAdapter adapter = FakeHttpAdapter(
      (RequestOptions o) => const FakeReply(200, _bundle),
    );
    final _MemoryCache cache = _MemoryCache();

    final Result<WorkScreen, Failure> result = await WorkScreenRepository(
      fakeDio(adapter),
      cache,
    ).load();

    expect(adapter.requests.single.path, '/screens/worker-work');
    final WorkScreen screen = result.okValue;
    expect(screen.standing.onTimeRate, 92);
    expect(screen.offers.single.quotedAmount, 25);
    expect(screen.assigned.single.budgetAmount, 60);
    expect(cache.entries, contains('screens.workerWork'));
  });

  test('offline, it shows the last copy instead of an error', () async {
    final _MemoryCache cache = _MemoryCache();
    await WorkScreenRepository(
      fakeDio(
        FakeHttpAdapter((RequestOptions o) => const FakeReply(200, _bundle)),
      ),
      cache,
    ).load();

    final Result<WorkScreen, Failure> offline = await WorkScreenRepository(
      fakeDio(FakeHttpAdapter(noSignal)),
      cache,
    ).load();

    expect(offline.okValue.assigned.single.id, 'job-2');
  });

  test("with nothing saved, it says why it couldn't load", () async {
    final Result<WorkScreen, Failure> result = await WorkScreenRepository(
      fakeDio(
        FakeHttpAdapter(
          (RequestOptions o) => const FakeReply(502, <String, Object?>{
            'detail': 'Database is down',
          }),
        ),
      ),
      _MemoryCache(),
    ).load();

    expect(result.errorValue.message, 'Database is down');
  });
}
