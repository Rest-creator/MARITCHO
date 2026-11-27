import 'package:equatable/equatable.dart';

class WorkerVetting extends Equatable {
  final String workerId;
  final String? idPhotoUrl;
  final String? idStatus; // PENDING, VERIFIED, REJECTED
  final String? idRejectionReason;
  final String? idVerifiedName;
  final String? policeClearanceUrl;
  final String? policeClearanceStatus;
  final String? policeClearanceRejectionReason;
  final bool hasPoliceClearance;
  final String grade;
  final int referenceCount;
  final int vouchCount;

  const WorkerVetting({
    required this.workerId,
    this.idPhotoUrl,
    this.idStatus,
    this.idRejectionReason,
    this.idVerifiedName,
    this.policeClearanceUrl,
    this.policeClearanceStatus,
    this.policeClearanceRejectionReason,
    this.hasPoliceClearance = false,
    this.grade = 'REGISTERED',
    this.referenceCount = 0,
    this.vouchCount = 0,
  });

  factory WorkerVetting.fromJson(Map<String, dynamic> json) {
    return WorkerVetting(
      workerId: json['worker_id'] as String,
      idPhotoUrl: json['id_photo_url'] as String?,
      idStatus: json['id_status'] as String?,
      idRejectionReason: json['id_rejection_reason'] as String?,
      idVerifiedName: json['id_verified_name'] as String?,
      policeClearanceUrl: json['police_clearance_url'] as String?,
      policeClearanceStatus: json['police_clearance_status'] as String?,
      policeClearanceRejectionReason:
          json['police_clearance_rejection_reason'] as String?,
      hasPoliceClearance: json['has_police_clearance'] as bool? ?? false,
      grade: json['grade'] as String? ?? 'REGISTERED',
      referenceCount: (json['reference_count'] as num?)?.toInt() ?? 0,
      vouchCount: (json['vouch_count'] as num?)?.toInt() ?? 0,
    );
  }

  @override
  List<Object?> get props => [
    workerId,
    idPhotoUrl,
    idStatus,
    idRejectionReason,
    idVerifiedName,
    policeClearanceUrl,
    policeClearanceStatus,
    hasPoliceClearance,
    grade,
    referenceCount,
    vouchCount,
  ];
}
