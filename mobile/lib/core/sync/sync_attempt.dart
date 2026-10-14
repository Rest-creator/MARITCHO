import 'package:equatable/equatable.dart';

/// What happened when one queued action was tried.
sealed class SyncAttempt extends Equatable {
  const SyncAttempt();
}

/// The backend has it.
final class Delivered extends SyncAttempt {
  const Delivered();

  @override
  List<Object?> get props => <Object?>[];
}

/// Not this time (no signal, server trouble, endpoint not built yet).
/// [after] overrides the usual backoff; [payload] saves progress made.
final class RetryLater extends SyncAttempt {
  final String reason;
  final Duration? after;
  final Map<String, Object?>? payload;

  const RetryLater(this.reason, {this.after, this.payload});

  @override
  List<Object?> get props => <Object?>[reason, after, payload];
}

/// The backend refused it and retrying won't change that.
final class Rejected extends SyncAttempt {
  final String reason;

  const Rejected(this.reason);

  @override
  List<Object?> get props => <Object?>[reason];
}
