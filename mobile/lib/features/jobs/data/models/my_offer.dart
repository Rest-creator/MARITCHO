import 'package:equatable/equatable.dart';
import 'package:mobile/core/json/json_number.dart';

/// Mirrors the backend's MyOfferOut.
class MyOffer extends Equatable {
  final String id;
  final String jobId;
  final double quotedAmount;
  final String? availabilityNote;
  final String jobTrade;
  final String jobSuburb;
  final String jobStatus;

  const MyOffer({
    required this.id,
    required this.jobId,
    required this.quotedAmount,
    required this.availabilityNote,
    required this.jobTrade,
    required this.jobSuburb,
    required this.jobStatus,
  });

  factory MyOffer.fromJson(Map<String, dynamic> json) {
    return MyOffer(
      id: json['id'] as String,
      jobId: json['job_id'] as String,
      quotedAmount: readRequiredDecimal(json['quoted_amount']),
      availabilityNote: json['availability_note'] as String?,
      jobTrade: json['job_trade'] as String,
      jobSuburb: json['job_suburb'] as String,
      jobStatus: json['job_status'] as String,
    );
  }

  @override
  List<Object?> get props => [
    id,
    jobId,
    quotedAmount,
    availabilityNote,
    jobTrade,
    jobSuburb,
    jobStatus,
  ];
}
