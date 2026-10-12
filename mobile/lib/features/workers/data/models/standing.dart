import 'package:equatable/equatable.dart';

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
      onTimeRate: (json['on_time_rate'] as num).toDouble(),
      disputeRate: (json['dispute_rate'] as num).toDouble(),
      fillRate: (json['fill_rate'] as num).toDouble(),
      jobsCompleted: json['jobs_completed'] as int,
      isFrozen: json['is_frozen'] as bool,
    );
  }

  @override
  List<Object?> get props => [grade, onTimeRate, disputeRate, fillRate, jobsCompleted, isFrozen];
}
