import 'package:equatable/equatable.dart';

class WorkerDirectoryItem extends Equatable {
  final String id;
  final String name;
  final String? phone;
  final String? suburb;
  final List<String> trades;
  final List<String> proofUrls;
  final String grade;
  final double onTimeRate;
  final double disputeRate;
  final double fillRate;
  final int jobsCompleted;
  final double? ratingAverage;
  final int ratingCount;
  final bool isAvailable;
  final int travelKm;
  final String? travelMeans;
  final String? distanceBand;
  final double? distanceKm;
  final bool hasPoliceClearance;

  const WorkerDirectoryItem({
    required this.id,
    required this.name,
    this.phone,
    this.suburb,
    required this.trades,
    this.proofUrls = const [],
    this.grade = 'REGISTERED',
    this.onTimeRate = 1.0,
    this.disputeRate = 0.0,
    this.fillRate = 1.0,
    this.jobsCompleted = 0,
    this.ratingAverage,
    this.ratingCount = 0,
    this.isAvailable = true,
    this.travelKm = 50,
    this.travelMeans,
    this.distanceBand,
    this.distanceKm,
    this.hasPoliceClearance = false,
  });

  factory WorkerDirectoryItem.fromJson(Map<String, dynamic> json) {
    return WorkerDirectoryItem(
      id: json['id'] as String,
      name: json['name'] as String? ?? 'Verified Worker',
      phone: json['phone'] as String?,
      suburb: json['suburb'] as String?,
      trades:
          (json['trades'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      proofUrls:
          (json['proof_urls'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      grade: json['grade'] as String? ?? 'REGISTERED',
      onTimeRate: (json['on_time_rate'] as num?)?.toDouble() ?? 1.0,
      disputeRate: (json['dispute_rate'] as num?)?.toDouble() ?? 0.0,
      fillRate: (json['fill_rate'] as num?)?.toDouble() ?? 1.0,
      jobsCompleted: (json['jobs_completed'] as num?)?.toInt() ?? 0,
      ratingAverage: (json['rating_average'] as num?)?.toDouble(),
      ratingCount: (json['rating_count'] as num?)?.toInt() ?? 0,
      isAvailable: json['is_available'] as bool? ?? true,
      travelKm: (json['travel_km'] as num?)?.toInt() ?? 50,
      travelMeans: json['travel_means'] as String?,
      distanceBand: json['distance_band'] as String?,
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
      hasPoliceClearance: json['has_police_clearance'] as bool? ?? false,
    );
  }

  @override
  List<Object?> get props => [
    id,
    name,
    phone,
    suburb,
    trades,
    grade,
    jobsCompleted,
    ratingAverage,
    isAvailable,
    distanceKm,
  ];
}

class WorkerPublicProfile extends WorkerDirectoryItem {
  final List<String> serviceAreas;
  final int referenceCount;

  const WorkerPublicProfile({
    required super.id,
    required super.name,
    super.phone,
    super.suburb,
    required super.trades,
    super.proofUrls,
    super.grade,
    super.onTimeRate,
    super.disputeRate,
    super.fillRate,
    super.jobsCompleted,
    super.ratingAverage,
    super.ratingCount,
    super.isAvailable,
    super.travelKm,
    super.travelMeans,
    super.distanceBand,
    super.distanceKm,
    super.hasPoliceClearance,
    this.serviceAreas = const [],
    this.referenceCount = 0,
  });

  factory WorkerPublicProfile.fromJson(Map<String, dynamic> json) {
    final base = WorkerDirectoryItem.fromJson(json);
    return WorkerPublicProfile(
      id: base.id,
      name: base.name,
      phone: base.phone,
      suburb: base.suburb,
      trades: base.trades,
      proofUrls: base.proofUrls,
      grade: base.grade,
      onTimeRate: base.onTimeRate,
      disputeRate: base.disputeRate,
      fillRate: base.fillRate,
      jobsCompleted: base.jobsCompleted,
      ratingAverage: base.ratingAverage,
      ratingCount: base.ratingCount,
      isAvailable: base.isAvailable,
      travelKm: base.travelKm,
      travelMeans: base.travelMeans,
      distanceBand: base.distanceBand,
      distanceKm: base.distanceKm,
      hasPoliceClearance: base.hasPoliceClearance,
      serviceAreas:
          (json['service_areas'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      referenceCount: (json['reference_count'] as num?)?.toInt() ?? 0,
    );
  }

  @override
  List<Object?> get props => [...super.props, serviceAreas, referenceCount];
}
