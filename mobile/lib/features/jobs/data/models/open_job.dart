import 'package:equatable/equatable.dart';
import 'package:mobile/core/json/json_number.dart';

/// Mirrors the backend's OpenJobOut — the pre-booking, address-hidden
/// shape a worker sees before submitting an offer. Distinct from Job
/// (the post-booking shape with full address).
class OpenJob extends Equatable {
  final String jobId;
  final String trade;
  final String suburb;
  final double? budgetAmount;
  final String? problemDescription;
  final String distanceBand;
  final double distanceKm;

  const OpenJob({
    required this.jobId,
    required this.trade,
    required this.suburb,
    required this.budgetAmount,
    required this.problemDescription,
    required this.distanceBand,
    required this.distanceKm,
  });

  factory OpenJob.fromJson(Map<String, dynamic> json) {
    return OpenJob(
      jobId: json['job_id'] as String,
      trade: json['trade'] as String,
      suburb: json['suburb'] as String,
      budgetAmount: readDecimal(json['budget_amount']),
      problemDescription: json['problem_description'] as String?,
      distanceBand: json['distance_band'] as String,
      distanceKm: readRequiredDecimal(json['distance_km']),
    );
  }

  @override
  List<Object?> get props => [
    jobId,
    trade,
    suburb,
    budgetAmount,
    problemDescription,
    distanceBand,
    distanceKm,
  ];
}
