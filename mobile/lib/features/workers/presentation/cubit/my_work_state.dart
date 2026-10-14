import 'package:equatable/equatable.dart';

import 'package:mobile/core/sync/outbox_item.dart';
import 'package:mobile/features/jobs/data/models/job.dart';
import 'package:mobile/features/jobs/data/models/my_offer.dart';
import 'package:mobile/features/workers/data/models/standing.dart';

abstract class MyWorkState extends Equatable {
  const MyWorkState();
  @override
  List<Object?> get props => <Object?>[];
}

class MyWorkInitial extends MyWorkState {}

class MyWorkLoading extends MyWorkState {}

class MyWorkLoaded extends MyWorkState {
  final Standing standing;
  final List<MyOffer> offers;
  final List<Job> assignedJobs;

  /// Work saved on the phone but not yet accepted by the backend, by job id.
  final Map<String, List<OutboxItem>> undelivered;

  /// A one-off message for the worker ("Price saved…"); shown once.
  final String? notice;

  const MyWorkLoaded({
    required this.standing,
    required this.offers,
    required this.assignedJobs,
    this.undelivered = const <String, List<OutboxItem>>{},
    this.notice,
  });

  List<Job> get activeJobs => assignedJobs
      .where((Job job) => job.status == 'BOOKED' || job.status == 'IN_PROGRESS')
      .toList();

  List<Job> get doneJobs =>
      assignedJobs.where((Job job) => job.status == 'COMPLETED').toList();

  /// The worker's own offer on [jobId], used to pre-fill the on-site price.
  double? offeredAmountFor(String jobId) {
    for (final MyOffer offer in offers) {
      if (offer.jobId == jobId) return offer.quotedAmount;
    }
    return null;
  }

  List<OutboxItem> undeliveredFor(String jobId) =>
      undelivered[jobId] ?? const <OutboxItem>[];

  MyWorkLoaded copyWith({
    List<MyOffer>? offers,
    List<Job>? assignedJobs,
    Standing? standing,
    Map<String, List<OutboxItem>>? undelivered,
    String? notice,
    bool clearNotice = false,
  }) {
    return MyWorkLoaded(
      standing: standing ?? this.standing,
      offers: offers ?? this.offers,
      assignedJobs: assignedJobs ?? this.assignedJobs,
      undelivered: undelivered ?? this.undelivered,
      notice: clearNotice ? null : (notice ?? this.notice),
    );
  }

  @override
  List<Object?> get props => <Object?>[
    standing,
    offers,
    assignedJobs,
    undelivered,
    notice,
  ];
}

class MyWorkFailure extends MyWorkState {
  final String errorMessage;
  const MyWorkFailure(this.errorMessage);
  @override
  List<Object?> get props => <Object?>[errorMessage];
}
