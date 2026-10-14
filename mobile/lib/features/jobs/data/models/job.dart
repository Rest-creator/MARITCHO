import 'package:equatable/equatable.dart';
import 'package:mobile/core/json/json_number.dart';

/// Mirrors the backend's JobOut / MyJobOut (JobOut plus an optional
/// offerCount — present only when fetched via GET /jobs/mine).
class Job extends Equatable {
  final String id;
  final String buyerId;
  final String? workerId;
  final String status;
  final String trade;
  final String suburb;
  final String address;
  final String? problemDescription;
  final double? budgetAmount;
  final String? currency;
  final double? quoteAmount;
  final DateTime createdAt;
  final int? offerCount;

  const Job({
    required this.id,
    required this.buyerId,
    required this.workerId,
    required this.status,
    required this.trade,
    required this.suburb,
    required this.address,
    required this.problemDescription,
    required this.budgetAmount,
    required this.currency,
    required this.quoteAmount,
    required this.createdAt,
    this.offerCount,
  });

  factory Job.fromJson(Map<String, dynamic> json) {
    return Job(
      id: json['id'] as String,
      buyerId: json['buyer_id'] as String,
      workerId: json['worker_id'] as String?,
      status: json['status'] as String,
      trade: json['trade'] as String,
      suburb: json['suburb'] as String,
      address: json['address'] as String,
      problemDescription: json['problem_description'] as String?,
      budgetAmount: readDecimal(json['budget_amount']),
      currency: json['currency'] as String?,
      quoteAmount: readDecimal(json['quote_amount']),
      createdAt: DateTime.parse(json['created_at'] as String),
      offerCount: json['offer_count'] as int?,
    );
  }

  @override
  List<Object?> get props => [
    id,
    buyerId,
    workerId,
    status,
    trade,
    suburb,
    address,
    problemDescription,
    budgetAmount,
    currency,
    quoteAmount,
    createdAt,
    offerCount,
  ];
}
