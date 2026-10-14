import 'package:equatable/equatable.dart';

import 'package:mobile/features/jobs/data/models/job.dart';
import 'package:mobile/features/jobs/data/models/my_offer.dart';
import 'package:mobile/features/workers/data/models/standing.dart';

/// Everything "My work" shows, from one BFF request
/// (`GET /api/screens/worker-work`, ADR-009 phase 2).
class WorkScreen extends Equatable {
  final Standing standing;
  final List<MyOffer> offers;
  final List<Job> assigned;

  const WorkScreen({
    required this.standing,
    required this.offers,
    required this.assigned,
  });

  factory WorkScreen.fromJson(Map<String, dynamic> json) {
    List<Map<String, dynamic>> list(String key) =>
        (json[key] as List<dynamic>).cast<Map<String, dynamic>>();
    return WorkScreen(
      standing: Standing.fromJson(json['standing'] as Map<String, dynamic>),
      offers: list('offers').map(MyOffer.fromJson).toList(),
      assigned: list('assigned').map(Job.fromJson).toList(),
    );
  }

  @override
  List<Object?> get props => <Object?>[standing, offers, assigned];
}
