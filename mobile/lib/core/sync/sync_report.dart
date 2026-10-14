import 'package:equatable/equatable.dart';

/// The result of one pass over the queue.
class SyncReport extends Equatable {
  final int delivered;
  final int postponed;
  final int rejected;

  /// True when another pass was already running and this one did nothing.
  final bool wasSkipped;

  const SyncReport({
    required this.delivered,
    required this.postponed,
    required this.rejected,
  }) : wasSkipped = false;

  const SyncReport.skipped()
    : delivered = 0,
      postponed = 0,
      rejected = 0,
      wasSkipped = true;

  bool get hasChanges => delivered > 0 || postponed > 0 || rejected > 0;

  @override
  List<Object?> get props => <Object?>[
    delivered,
    postponed,
    rejected,
    wasSkipped,
  ];
}
