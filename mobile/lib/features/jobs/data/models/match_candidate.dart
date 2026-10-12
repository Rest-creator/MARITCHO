import 'package:equatable/equatable.dart';

/// Mirrors the backend's MatchCandidateOut.
class MatchCandidate extends Equatable {
  final String workerId;
  final String suburb;
  final String distanceBand;
  final double distanceKm;
  final String grade;
  final double onTimeRate;
  final int jobsCompleted;
  final String reason;
  final double? quotedAmount;
  final String? availabilityNote;

  const MatchCandidate({
    required this.workerId,
    required this.suburb,
    required this.distanceBand,
    required this.distanceKm,
    required this.grade,
    required this.onTimeRate,
    required this.jobsCompleted,
    required this.reason,
    required this.quotedAmount,
    required this.availabilityNote,
  });

  factory MatchCandidate.fromJson(Map<String, dynamic> json) {
    return MatchCandidate(
      workerId: json['worker_id'] as String,
      suburb: json['suburb'] as String,
      distanceBand: json['distance_band'] as String,
      distanceKm: (json['distance_km'] as num).toDouble(),
      grade: json['grade'] as String,
      onTimeRate: (json['on_time_rate'] as num).toDouble(),
      jobsCompleted: json['jobs_completed'] as int,
      reason: json['reason'] as String,
      quotedAmount: (json['quoted_amount'] as num?)?.toDouble(),
      availabilityNote: json['availability_note'] as String?,
    );
  }

  @override
  List<Object?> get props => [
    workerId,
    suburb,
    distanceBand,
    distanceKm,
    grade,
    onTimeRate,
    jobsCompleted,
    reason,
    quotedAmount,
    availabilityNote,
  ];
}
