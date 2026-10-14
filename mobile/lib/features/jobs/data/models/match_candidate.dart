import 'package:equatable/equatable.dart';
import 'package:mobile/core/json/json_number.dart';

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
      distanceKm: readRequiredDecimal(json['distance_km']),
      grade: json['grade'] as String,
      onTimeRate: readRequiredDecimal(json['on_time_rate']),
      jobsCompleted: json['jobs_completed'] as int,
      reason: json['reason'] as String,
      quotedAmount: readDecimal(json['quoted_amount']),
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
