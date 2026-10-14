import 'dart:io';
import 'dart:math';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/sync/outbox_actions.dart';
import 'package:mobile/core/sync/outbox_item.dart';
import 'package:mobile/core/sync/sync_attempt.dart';
import 'package:mobile/core/sync/sync_report.dart';
import 'package:mobile/core/sync/sync_service.dart';

import '../../support/fake_http_adapter.dart';
import '../../support/fake_outbox.dart';

final DateTime _now = DateTime.utc(2026, 10, 14, 9, 30);

SyncService _service(
  FakeOutbox outbox,
  FakeHttpAdapter adapter, {
  List<String>? removed,
}) {
  return SyncService(
    outbox,
    fakeDio(adapter),
    now: () => _now,
    random: Random(1),
    removeFile: (String path) async => removed?.add(path),
  );
}

Future<int> _queueQuote(FakeOutbox outbox, {String jobId = 'job-1'}) =>
    outbox.enqueue(
      type: OutboxActions.submitQuote,
      jobId: jobId,
      payload: <String, Object?>{
        'job_id': jobId,
        'labor_amount': 40.0,
        'materials_amount': 5.0,
      },
    );

void main() {
  group('backoff', () {
    test('starts at 30 s, doubles, and stops growing at 15 min', () {
      final Random random = Random(1);
      expect(
        SyncService.backoffFor(1, random).inSeconds,
        inInclusiveRange(30, 36),
      );
      expect(
        SyncService.backoffFor(2, random).inSeconds,
        inInclusiveRange(60, 72),
      );
      expect(
        SyncService.backoffFor(20, random).inMinutes,
        inInclusiveRange(15, 18),
      );
    });
  });

  group('classify', () {
    DioException failed(int? status, [Object? body]) => DioException(
      requestOptions: RequestOptions(path: '/x'),
      type: status == null
          ? DioExceptionType.connectionError
          : DioExceptionType.badResponse,
      response: status == null
          ? null
          : Response<Object?>(
              requestOptions: RequestOptions(path: '/x'),
              statusCode: status,
              data: body,
            ),
    );

    test('no signal and server trouble are retried', () {
      expect(SyncService.classify(failed(null)), isA<RetryLater>());
      expect(SyncService.classify(failed(503)), isA<RetryLater>());
      expect(SyncService.classify(failed(401)), isA<RetryLater>());
    });

    test('a conflict means the backend already has it', () {
      expect(SyncService.classify(failed(409)), const Delivered());
    });

    test("a refusal keeps the backend's reason", () {
      expect(
        SyncService.classify(
          failed(400, <String, Object?>{'detail': 'Quote must exceed deposit'}),
        ),
        const Rejected('Quote must exceed deposit'),
      );
      expect(
        SyncService.classify(
          failed(422, <String, Object?>{
            'detail': <Object?>[
              <String, Object?>{'msg': 'Input should be greater than 0'},
            ],
          }),
        ),
        const Rejected('Input should be greater than 0'),
      );
    });
  });

  group('processQueue', () {
    test(
      'sends a queued price to /jobs/{id}/quote and marks it sent',
      () async {
        final FakeOutbox outbox = FakeOutbox();
        final FakeHttpAdapter adapter = FakeHttpAdapter(
          (RequestOptions o) => const FakeReply(200, <String, Object?>{}),
        );
        final int id = await _queueQuote(outbox);

        final SyncReport report = await _service(
          outbox,
          adapter,
        ).processQueue();

        expect(
          report,
          const SyncReport(delivered: 1, postponed: 0, rejected: 0),
        );
        expect(adapter.requests.single.path, '/jobs/job-1/quote');
        expect(adapter.requests.single.data, <String, Object?>{
          'labor_amount': 40.0,
          'materials_amount': 5.0,
        });
        expect(outbox.items[id]!.status, OutboxStatus.sent);
      },
    );

    test('without signal it keeps the item and schedules a retry, without blocking', () async {
      final FakeOutbox outbox = FakeOutbox();
      final FakeHttpAdapter adapter = FakeHttpAdapter(noSignal);
      final int first = await _queueQuote(outbox, jobId: 'job-1');
      final int second = await _queueQuote(outbox, jobId: 'job-2');

      final Stopwatch clock = Stopwatch()..start();
      final SyncReport report = await _service(outbox, adapter).processQueue();

      expect(
        clock.elapsed,
        lessThan(const Duration(seconds: 2)),
        reason: 'no waiting in the loop',
      );
      expect(report.postponed, 2);
      expect(
        adapter.requests,
        hasLength(2),
        reason: 'one failure must not hold up the rest',
      );
      for (final int id in <int>[first, second]) {
        final OutboxItem item = outbox.items[id]!;
        expect(item.status, OutboxStatus.pending);
        expect(item.attempts, 1);
        expect(item.nextAttemptAt!.isAfter(_now), isTrue);
        expect(item.lastError, contains('No signal'));
      }
      expect(
        await outbox.due(_now),
        isEmpty,
        reason: 'not tried again before its time',
      );
    });

    test('a refused price is kept with the reason, not dropped', () async {
      final FakeOutbox outbox = FakeOutbox();
      final FakeHttpAdapter adapter = FakeHttpAdapter(
        (RequestOptions o) => const FakeReply(400, <String, Object?>{
          'detail': 'Quote must exceed deposit',
        }),
      );
      final int id = await _queueQuote(outbox);

      await _service(outbox, adapter).processQueue();

      expect(outbox.items[id]!.status, OutboxStatus.failed);
      expect(outbox.items[id]!.lastError, 'Quote must exceed deposit');
      expect(await outbox.undeliveredForJob('job-1'), hasLength(1));
    });

    test('tells listeners when something changed', () async {
      final FakeOutbox outbox = FakeOutbox();
      final SyncService service = _service(
        outbox,
        FakeHttpAdapter(
          (RequestOptions o) => const FakeReply(200, <String, Object?>{}),
        ),
      );
      await _queueQuote(outbox);
      final Future<void> changed = service.changes.first;
      await service.processQueue();
      await expectLater(changed, completes);
      await service.dispose();
    });

    group('photos', () {
      late Directory dir;
      late String photoPath;

      setUp(() async {
        dir = await Directory.systemTemp.createTemp('outbox_test');
        photoPath = '${dir.path}/p.jpg';
        await File(photoPath).writeAsBytes(<int>[0xff, 0xd8, 0xff, 0xd9]);
      });

      tearDown(() async {
        if (await dir.exists()) await dir.delete(recursive: true);
      });

      Future<int> queuePhoto(FakeOutbox outbox) => outbox.enqueue(
        type: OutboxActions.sendPhoto,
        jobId: 'job-1',
        payload: <String, Object?>{
          'job_id': 'job-1',
          'file_path': photoPath,
          'upload_key': 'k1',
        },
      );

      test('uploads, posts it to the job chat, then tidies the file', () async {
        final FakeOutbox outbox = FakeOutbox();
        final FakeHttpAdapter adapter = FakeHttpAdapter(
          (RequestOptions o) => o.path == '/media'
              ? const FakeReply(201, <String, Object?>{
                  'url': '/media/p1.jpg',
                  'content_type': 'image/jpeg',
                  'size_bytes': 4,
                })
              : const FakeReply(201, <String, Object?>{}),
        );
        final List<String> removed = <String>[];
        final int id = await queuePhoto(outbox);

        await _service(outbox, adapter, removed: removed).processQueue();

        expect(adapter.requests.map((RequestOptions o) => o.path), <String>[
          '/media',
          '/jobs/job-1/messages',
        ]);
        expect(adapter.requests.first.headers['Idempotency-Key'], 'k1');
        expect(adapter.requests.last.data, <String, Object?>{
          'message_type': 'PHOTO',
          'media_url': '/media/p1.jpg',
        });
        expect(outbox.items[id]!.status, OutboxStatus.sent);
        expect(removed, <String>[photoPath]);
      });

      test(
        'waits an hour while the backend has no upload endpoint (issue #1)',
        () async {
          final FakeOutbox outbox = FakeOutbox();
          final FakeHttpAdapter adapter = FakeHttpAdapter(
            (RequestOptions o) =>
                const FakeReply(404, <String, Object?>{'detail': 'Not Found'}),
          );
          final int id = await queuePhoto(outbox);

          await _service(outbox, adapter).processQueue();

          final OutboxItem item = outbox.items[id]!;
          expect(
            item.status,
            OutboxStatus.pending,
            reason: 'not a failure — just not built yet',
          );
          expect(
            item.nextAttemptAt,
            _now.add(SyncService.waitForMissingEndpoint),
          );
          expect(item.lastError, contains("can't be sent yet"));
          expect(
            await File(photoPath).exists(),
            isTrue,
            reason: 'the photo is kept',
          );
        },
      );

      test('keeps the upload when only the chat message failed', () async {
        final FakeOutbox outbox = FakeOutbox();
        final FakeHttpAdapter adapter = FakeHttpAdapter((RequestOptions o) {
          if (o.path == '/media') {
            return const FakeReply(201, <String, Object?>{
              'url': '/media/p1.jpg',
              'content_type': 'image/jpeg',
              'size_bytes': 4,
            });
          }
          return noSignal(o);
        });
        final int id = await queuePhoto(outbox);

        await _service(outbox, adapter).processQueue();

        expect(outbox.items[id]!.payload['media_url'], '/media/p1.jpg');
        expect(outbox.items[id]!.status, OutboxStatus.pending);
      });

      test(
        'a photo deleted from the phone is reported, not retried forever',
        () async {
          final FakeOutbox outbox = FakeOutbox();
          final int id = await queuePhoto(outbox);
          await File(photoPath).delete();

          await _service(
            outbox,
            FakeHttpAdapter(
              (RequestOptions o) => const FakeReply(201, <String, Object?>{}),
            ),
          ).processQueue();

          expect(outbox.items[id]!.status, OutboxStatus.failed);
          expect(
            outbox.items[id]!.lastError,
            contains('no longer on this phone'),
          );
        },
      );
    });
  });
}
