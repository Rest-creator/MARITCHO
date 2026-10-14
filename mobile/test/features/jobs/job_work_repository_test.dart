import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/core/sync/outbox_actions.dart';
import 'package:mobile/core/sync/outbox_item.dart';
import 'package:mobile/features/jobs/data/repositories/job_work_repository.dart';

import '../../support/fake_outbox.dart';

void main() {
  late FakeOutbox outbox;
  late Directory photos;
  late int nudges;
  late JobWorkRepository repository;

  setUp(() async {
    outbox = FakeOutbox();
    photos = await Directory.systemTemp.createTemp('kept_photos');
    nudges = 0;
    repository = JobWorkRepository(
      outbox,
      onQueued: () => nudges++,
      photoDirectory: () async => Directory('${photos.path}/outbox_photos'),
    );
  });

  tearDown(() async {
    if (await photos.exists()) await photos.delete(recursive: true);
  });

  group('queueQuote', () {
    test('saves the price rounded to cents and asks for a send', () async {
      final Result<void, Failure> result = await repository.queueQuote(
        jobId: 'job-1',
        laborAmount: 40.004,
        materialsAmount: 5.5,
      );

      expect(result.isOk, isTrue);
      final OutboxItem item = outbox.items.values.single;
      expect(item.type, OutboxActions.submitQuote);
      expect(item.jobId, 'job-1');
      expect(item.payload, <String, Object?>{
        'job_id': 'job-1',
        'labor_amount': 40.0,
        'materials_amount': 5.5,
      });
      expect(nudges, 1);
    });

    test('refuses a price of nothing, or negative materials', () async {
      final Result<void, Failure> zero = await repository.queueQuote(
        jobId: 'job-1',
        laborAmount: 0,
        materialsAmount: 0,
      );
      final Result<void, Failure> negative = await repository.queueQuote(
        jobId: 'job-1',
        laborAmount: 10,
        materialsAmount: -1,
      );

      expect(zero.errorValue, isA<ValidationFailure>());
      expect(negative.errorValue, isA<ValidationFailure>());
      expect(outbox.items, isEmpty);
      expect(nudges, 0);
    });
  });

  group('queuePhoto', () {
    test(
      "copies the camera's temporary file into the app's own storage",
      () async {
        final File cameraFile = File('${photos.path}/camera_tmp.jpg');
        await cameraFile.writeAsBytes(<int>[1, 2, 3]);

        final Result<void, Failure> result = await repository.queuePhoto(
          jobId: 'job-1',
          sourcePath: cameraFile.path,
        );

        expect(result.isOk, isTrue);
        final OutboxItem item = outbox.items.values.single;
        final String kept = item.payload['file_path']! as String;
        expect(kept, contains('outbox_photos'));
        expect(await File(kept).readAsBytes(), <int>[1, 2, 3]);
        expect(item.payload['upload_key'], matches(RegExp(r'^[0-9a-f]{32}$')));
        expect(nudges, 1);
      },
    );

    test('reports a photo that cannot be read', () async {
      final Result<void, Failure> result = await repository.queuePhoto(
        jobId: 'job-1',
        sourcePath: '${photos.path}/missing.jpg',
      );

      expect(result.errorValue, isA<StorageFailure>());
      expect(outbox.items, isEmpty);
    });
  });

  test(
    'retry puts a refused item back in line and sends straight away',
    () async {
      final int id = await outbox.enqueue(
        type: OutboxActions.submitQuote,
        jobId: 'job-1',
        payload: <String, Object?>{},
      );
      await outbox.markFailed(id, error: 'Quote must exceed deposit');

      await repository.retry(id);

      expect(outbox.items[id]!.status, OutboxStatus.pending);
      expect(outbox.items[id]!.lastError, isNull);
      expect(nudges, 1);
    },
  );
}
