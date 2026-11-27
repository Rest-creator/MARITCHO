import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/core/theme/app_theme.dart';

import '../../data/models/job.dart';
import '../../data/repositories/jobs_repository.dart';
import '../cubit/job_tracking_cubit.dart';
import '../cubit/job_tracking_state.dart';
import '../widgets/dispute_sheet.dart';
import '../widgets/review_panel.dart';

/// Ports JobTracking screen with status, in-job messaging, dispute sheet,
/// completion confirmation, and structured review (stars + tags).
class JobTrackingPage extends StatelessWidget {
  final Job job;

  const JobTrackingPage({super.key, required this.job});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) => JobTrackingCubit(ctx.read<JobsRepository>()),
      child: _JobTrackingView(job: job),
    );
  }
}

class _JobTrackingView extends StatefulWidget {
  final Job job;

  const _JobTrackingView({required this.job});

  @override
  State<_JobTrackingView> createState() => _JobTrackingViewState();
}

class _JobTrackingViewState extends State<_JobTrackingView> {
  final _whatWasDoneController = TextEditingController();
  final _commentController = TextEditingController();
  final ReviewDraft _reviewDraft = ReviewDraft();

  bool _isDisputed = false;

  @override
  void initState() {
    super.initState();
    _isDisputed = widget.job.status == 'DISPUTED';
  }

  @override
  void dispose() {
    _whatWasDoneController.dispose();
    _commentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.job.trade),
        actions: [
          IconButton(
            icon: const Icon(Icons.chat_bubble_outline),
            tooltip: 'Open Chat',
            onPressed: () {
              Navigator.of(context).pushNamed(
                '/chat',
                arguments: {
                  'jobId': widget.job.id,
                  'jobTitle': widget.job.trade,
                },
              );
            },
          ),
        ],
      ),
      body: BlocConsumer<JobTrackingCubit, JobTrackingState>(
        listener: (context, state) {
          if (!mounted) return;

          if (state is JobTrackingSuccess) {
            _submitPostCompletionReview();
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Job confirmed done & payment released.'),
              ),
            );
            Navigator.of(context).popUntil((route) => route.isFirst);
          } else if (state is JobTrackingFailure) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.errorMessage),
                backgroundColor: Colors.red,
              ),
            );
          }
        },
        builder: (context, state) {
          final isSubmitting = state is JobTrackingSubmitting;
          final canComplete =
              widget.job.status == 'IN_PROGRESS' && !_isDisputed;

          return Padding(
            padding: const EdgeInsets.all(20),
            child: ListView(
              children: [
                _buildStatusBanner(),
                const SizedBox(height: 12),
                Text('Location: ${widget.job.suburb}'),
                const SizedBox(height: 16),
                Card(
                  child: ListTile(
                    leading: const Icon(Icons.chat, color: Colors.blueGrey),
                    title: const Text('Message worker'),
                    subtitle: const Text(
                      'Discuss job, arrival or instructions',
                    ),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () {
                      Navigator.of(context).pushNamed(
                        '/chat',
                        arguments: {
                          'jobId': widget.job.id,
                          'jobTitle': widget.job.trade,
                        },
                      );
                    },
                  ),
                ),
                const SizedBox(height: 20),
                if (canComplete) ...[
                  TextField(
                    controller: _whatWasDoneController,
                    decoration: const InputDecoration(
                      labelText: 'What was done',
                      hintText: 'e.g. Fixed leaking sink pipe under counter',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  ReviewPanel(
                    draft: _reviewDraft,
                    onChanged: (updated) {
                      setState(() {});
                    },
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _commentController,
                    decoration: const InputDecoration(
                      labelText: 'Review comment (Optional)',
                      hintText: 'Any words for the worker...',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      backgroundColor: AppTheme.primaryBlueGray,
                      foregroundColor: Colors.white,
                    ),
                    onPressed: isSubmitting ? null : _confirmDone,
                    child: isSubmitting
                        ? const CircularProgressIndicator(color: Colors.white)
                        : const Text(
                            'Confirm Done & Release Payment',
                            style: TextStyle(fontWeight: FontWeight.bold),
                          ),
                  ),
                  const SizedBox(height: 16),
                  Center(
                    child: TextButton.icon(
                      style: TextButton.styleFrom(
                        foregroundColor: Colors.red.shade700,
                      ),
                      icon: const Icon(Icons.warning_amber),
                      label: const Text("Something's not right? Raise concern"),
                      onPressed: () {
                        DisputeSheet.show(
                          context,
                          jobId: widget.job.id,
                          jobsRepository: context.read<JobsRepository>(),
                          onDisputeRaised: () {
                            setState(() {
                              _isDisputed = true;
                            });
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text(
                                  'Concern reported. Payment frozen.',
                                ),
                              ),
                            );
                          },
                        );
                      },
                    ),
                  ),
                ] else if (_isDisputed) ...[
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.red.shade200),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.lock, color: Colors.red.shade700),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Text(
                            'Payment is frozen while this concern is open. The worker has been notified to respond.',
                            style: TextStyle(fontSize: 13),
                          ),
                        ),
                      ],
                    ),
                  ),
                ] else ...[
                  const Text('Payment is locked until the job is in progress.'),
                ],
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildStatusBanner() {
    final statusText = _isDisputed ? 'DISPUTED' : widget.job.status;
    final color = _isDisputed ? Colors.red.shade700 : AppTheme.primaryBlueGray;

    return Row(
      children: [
        Text('Status: ', style: Theme.of(context).textTheme.titleMedium),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            statusText,
            style: TextStyle(color: color, fontWeight: FontWeight.bold),
          ),
        ),
      ],
    );
  }

  void _confirmDone() {
    final whatDone = _whatWasDoneController.text.trim();
    if (whatDone.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please describe what was done.')),
      );
      return;
    }

    context.read<JobTrackingCubit>().completeJob(
      jobId: widget.job.id,
      whatWasDone: whatDone,
      clientWords: _commentController.text.isNotEmpty
          ? _commentController.text
          : null,
    );
  }

  void _submitPostCompletionReview() {
    final repo = context.read<JobsRepository>();
    repo.submitReview(
      jobId: widget.job.id,
      rating: _reviewDraft.rating,
      tags: _reviewDraft.tags,
      comment: _commentController.text.isNotEmpty
          ? _commentController.text
          : null,
    );
  }
}
