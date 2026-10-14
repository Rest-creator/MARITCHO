import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/json/json_number.dart';
import 'package:mobile/features/jobs/data/models/job.dart';
import 'package:mobile/features/jobs/data/models/my_offer.dart';
import 'package:mobile/features/suburbs/data/models/suburb.dart';

void main() {
  group('readDecimal', () {
    test('reads the strings Pydantic sends for Decimal fields', () {
      expect(readDecimal('40.00'), 40.0);
      expect(readDecimal(' 12.5 '), 12.5);
      expect(readDecimal('-20.185000'), -20.185);
    });

    test('reads plain numbers too', () {
      expect(readDecimal(3), 3.0);
      expect(readDecimal(0.8), 0.8);
    });

    test('null or rubbish is null, and required fields fall back', () {
      expect(readDecimal(null), isNull);
      expect(readDecimal('abc'), isNull);
      expect(readRequiredDecimal(null), 0);
      expect(readRequiredDecimal('abc', fallback: 100), 100);
    });
  });

  group('models parse what the real backend sends', () {
    test('a job with a string budget and quote', () {
      final Job job = Job.fromJson(<String, dynamic>{
        'id': 'job-1',
        'buyer_id': 'b-1',
        'worker_id': 'w-1',
        'status': 'IN_PROGRESS',
        'trade': 'PLUMBING',
        'suburb': 'Hillside',
        'address': '14 Harrow Rd',
        'problem_description': 'Leaking tap',
        'budget_amount': '40.00',
        'currency': 'USD',
        'quote_amount': '45.00',
        'created_at': '2026-10-14T06:26:49.374416Z',
      });
      expect(job.budgetAmount, 40.0);
      expect(job.quoteAmount, 45.0);
    });

    test('an offer and a suburb', () {
      final MyOffer offer = MyOffer.fromJson(<String, dynamic>{
        'id': 'o-1',
        'job_id': 'job-1',
        'quoted_amount': '25.50',
        'availability_note': null,
        'job_trade': 'ELECTRICAL',
        'job_suburb': 'Kumalo',
        'job_status': 'MATCHED',
      });
      expect(offer.quotedAmount, 25.5);

      final Suburb suburb = Suburb.fromJson(<String, dynamic>{
        'name': 'Entumbane',
        'latitude': '-20.220000',
        'longitude': '28.550000',
      });
      expect(suburb.latitude, -20.22);
      expect(suburb.longitude, 28.55);
    });
  });
}
