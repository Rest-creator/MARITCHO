import 'package:flutter/material.dart';

import 'package:mobile/core/sync/outbox_actions.dart';
import 'package:mobile/core/sync/outbox_item.dart';
import 'package:mobile/core/theme/app_theme.dart';
import 'package:mobile/features/jobs/data/models/job.dart';

/// A hired job on My work: where it is, what's waiting to send, and what
/// to do next — "I've arrived" (confirm the price) while booked, and
/// photos while on site.
class ActiveJobCard extends StatelessWidget {
  final Job job;
  final List<OutboxItem> undelivered;
  final VoidCallback onArrived;
  final VoidCallback onAddPhoto;
  final ValueChanged<int> onRetry;

  const ActiveJobCard({
    super.key,
    required this.job,
    required this.undelivered,
    required this.onArrived,
    required this.onAddPhoto,
    required this.onRetry,
  });

  bool get _hasQueuedPrice => undelivered.any(
    (OutboxItem item) =>
        item.type == OutboxActions.submitQuote &&
        item.status == OutboxStatus.pending,
  );

  @override
  Widget build(BuildContext context) {
    final bool isBooked = job.status == 'BOOKED';
    final String headline = (job.problemDescription ?? '')
        .split('\n')
        .first
        .trim();
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Expanded(
                  child: Text(
                    isBooked ? 'You got the job' : 'Price agreed · working',
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      color: AppTheme.darkBlueGray,
                    ),
                  ),
                ),
                if (job.quoteAmount != null)
                  Text(
                    '\$${job.quoteAmount!.toStringAsFixed(2)}',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              headline.isEmpty ? job.trade : headline,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            Text(
              '${job.address}, ${job.suburb}',
              style: const TextStyle(color: AppTheme.coolGray),
            ),
            for (final OutboxItem item in undelivered) ...<Widget>[
              const SizedBox(height: 8),
              _UndeliveredLine(item: item, onRetry: () => onRetry(item.id)),
            ],
            const SizedBox(height: 12),
            Row(
              children: <Widget>[
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: onAddPhoto,
                    icon: const Icon(Icons.photo_camera_outlined),
                    label: const Text('Add photo'),
                  ),
                ),
                if (isBooked) ...<Widget>[
                  const SizedBox(width: 10),
                  Expanded(
                    child: FilledButton(
                      onPressed: _hasQueuedPrice ? null : onArrived,
                      child: Text(
                        _hasQueuedPrice ? 'Price saved' : "I've arrived",
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// "Saved, sends when there's signal" — or why the backend refused it.
class _UndeliveredLine extends StatelessWidget {
  final OutboxItem item;
  final VoidCallback onRetry;

  const _UndeliveredLine({required this.item, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final String what = item.type == OutboxActions.submitQuote
        ? 'Price'
        : 'Photo';
    final bool hasFailed = item.status == OutboxStatus.failed;
    final Color color = hasFailed
        ? Theme.of(context).colorScheme.error
        : AppTheme.darkBlueGray;
    final String text = hasFailed
        ? '$what not sent: ${item.lastError ?? 'refused'}'
        : '$what saved on your phone. ${item.lastError ?? 'Sending…'}';
    return Semantics(
      liveRegion: true,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(
            hasFailed ? Icons.error_outline : Icons.schedule,
            size: 18,
            color: color,
          ),
          const SizedBox(width: 6),
          Expanded(
            child: Text(text, style: TextStyle(fontSize: 13, color: color)),
          ),
          if (hasFailed)
            TextButton(onPressed: onRetry, child: const Text('Try again')),
        ],
      ),
    );
  }
}
