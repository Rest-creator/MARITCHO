import 'package:equatable/equatable.dart';

/// Where a queued action is in its life.
enum OutboxStatus {
  /// Waiting to be sent (now, or at [OutboxItem.nextAttemptAt]).
  pending,

  /// Delivered; kept briefly only so the UI can stop showing it.
  sent,

  /// The backend refused it for good (e.g. the price is below the deposit).
  /// Kept with its reason so the worker sees it — never silently dropped.
  failed,
}

/// One action saved on the phone until the backend has it.
class OutboxItem extends Equatable {
  final int id;
  final String type;
  final String? jobId;
  final Map<String, Object?> payload;
  final OutboxStatus status;
  final int attempts;
  final DateTime createdAt;
  final DateTime? nextAttemptAt;
  final String? lastError;

  const OutboxItem({
    required this.id,
    required this.type,
    required this.jobId,
    required this.payload,
    required this.status,
    required this.attempts,
    required this.createdAt,
    required this.nextAttemptAt,
    required this.lastError,
  });

  bool isDue(DateTime now) =>
      status == OutboxStatus.pending &&
      (nextAttemptAt == null || !nextAttemptAt!.isAfter(now));

  @override
  List<Object?> get props => <Object?>[
    id,
    type,
    jobId,
    payload,
    status,
    attempts,
    createdAt,
    nextAttemptAt,
    lastError,
  ];
}
