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
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppTheme.lightBlueGray),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Expanded(
                  child: Text(
                    job.trade,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(
                    Icons.chat_bubble_outline,
                    color: AppTheme.primaryBlueGray,
                  ),
                  tooltip: 'Chat with employer',
                  onPressed: () {
                    Navigator.of(context).pushNamed(
                      '/chat',
                      arguments: {'jobId': job.id, 'jobTitle': job.trade},
                    );
                  },
                ),
                _statusBadge(job.status),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              job.suburb,
              style: TextStyle(
                color: AppTheme.darkBlueGray.withValues(alpha: 0.7),
                fontSize: 13,
              ),
            ),
            if (headline.isNotEmpty) ...<Widget>[
              const SizedBox(height: 8),
              Text(
                headline,
                style: const TextStyle(
                  fontSize: 14,
                  color: AppTheme.darkBlueGray,
                ),
              ),
            ],
            if (undelivered.isNotEmpty) ...<Widget>[
              const SizedBox(height: 12),
              _outboxSection(context),
            ],
            const SizedBox(height: 12),
            if (isBooked)
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  style: FilledButton.styleFrom(
                    backgroundColor: AppTheme.primaryBlueGray,
                  ),
                  onPressed: _hasQueuedPrice ? null : onArrived,
                  icon: const Icon(Icons.pin_drop_outlined),
                  label: Text(
                    _hasQueuedPrice
                        ? "Price saved — waiting for signal"
                        : "I've arrived · Confirm price",
                  ),
                ),
              )
            else if (job.status == 'COMPLETED')
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () {
                        Navigator.of(context)
                            .pushNamed('/worker-review-client', arguments: job);
                      },
                      icon: const Icon(Icons.star_outline),
                      label: const Text('Rate client'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  OutlinedButton.icon(
                    onPressed: () {
                      Navigator.of(context).pushNamed(
                        '/chat',
                        arguments: {'jobId': job.id, 'jobTitle': job.trade},
                      );
                    },
                    icon: const Icon(Icons.chat),
                    label: const Text('Chat'),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }

  Widget _statusBadge(String status) {
    final (String label, Color color) = switch (status) {
      'BOOKED' => ('Booked', Colors.amber.shade800),
      'IN_PROGRESS' => ('On site', AppTheme.primaryBlueGray),
      'COMPLETED' => ('Finished', Colors.green.shade700),
      _ => (status, AppTheme.darkBlueGray),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  Widget _outboxSection(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppTheme.lightBlueGray.withValues(alpha: 0.25),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          for (final OutboxItem item in undelivered) ...<Widget>[
            Row(
              children: <Widget>[
                Icon(
                  item.status == OutboxStatus.failed
                      ? Icons.error_outline
                      : Icons.schedule,
                  size: 16,
                  color: item.status == OutboxStatus.failed
                      ? Colors.red.shade700
                      : AppTheme.primaryBlueGray,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    _itemSummary(item),
                    style: const TextStyle(fontSize: 12),
                  ),
                ),
                if (item.status == OutboxStatus.failed)
                  TextButton(
                    onPressed: () => onRetry(item.id),
                    child: const Text('Retry now'),
                  ),
              ],
            ),
            if (item.lastError != null)
              Padding(
                padding: const EdgeInsets.only(left: 22, top: 2),
                child: Text(
                  item.lastError!,
                  style: TextStyle(fontSize: 11, color: Colors.red.shade800),
                ),
              ),
          ],
        ],
      ),
    );
  }

  String _itemSummary(OutboxItem item) {
    return switch (item.type) {
      OutboxActions.submitQuote => 'Price update queued',
      OutboxActions.sendPhoto => 'Job photo queued',
      _ => 'Update queued',
    };
  }
}
