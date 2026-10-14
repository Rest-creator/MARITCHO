import 'dart:async';

import 'package:flutter/widgets.dart';

import 'package:mobile/core/sync/sync_service.dart';

/// Decides when the queue is sent: at start-up, whenever the app comes
/// back to the foreground (often right after the phone found signal),
/// once a minute while it is open, and straight after new work is queued.
/// A timer instead of a connectivity plugin keeps the app small; each
/// pass is cheap when nothing is due.
class SyncScheduler with WidgetsBindingObserver {
  final SyncService _syncService;
  final Duration _interval;
  Timer? _timer;

  SyncScheduler(
    this._syncService, {
    this._interval = const Duration(minutes: 1),
  });

  void start() {
    WidgetsBinding.instance.addObserver(this);
    _timer = Timer.periodic(_interval, (Timer _) => nudge());
    nudge();
  }

  /// Send now (e.g. right after something was queued).
  void nudge() {
    unawaited(_syncService.processQueue());
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) nudge();
  }

  void dispose() {
    _timer?.cancel();
    _timer = null;
    WidgetsBinding.instance.removeObserver(this);
  }
}
