import 'package:equatable/equatable.dart';
import 'package:mobile/core/json/json_number.dart';

/// Mirrors the backend's StandingOut.
class Standing extends Equatable {
  final String grade;
  final double onTimeRate;
  final double disputeRate;
  final double fillRate;
  final int jobsCompleted;
  final bool isFrozen;

  const Standing({
    required this.grade,
    required this.onTimeRate,
    required this.disputeRate,
    required this.fillRate,
    required this.jobsCompleted,
    required this.isFrozen,
  });

  factory Standing.fromJson(Map<String, dynamic> json) {
    return Standing(
      grade: json['grade'] as String,
      onTimeRate: readRequiredDecimal(json['on_time_rate']),
      disputeRate: readRequiredDecimal(json['dispute_rate']),
      fillRate: readRequiredDecimal(json['fill_rate']),
      jobsCompleted: json['jobs_completed'] as int,
      isFrozen: json['is_frozen'] as bool,
    );
  }

  @override
  List<Object?> get props => [
    grade,
    onTimeRate,
    disputeRate,
    fillRate,
    jobsCompleted,
    isFrozen,
  ];
}
