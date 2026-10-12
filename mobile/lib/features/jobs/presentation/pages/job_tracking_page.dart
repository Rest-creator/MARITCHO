import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/models/job.dart';
import '../../data/repositories/jobs_repository.dart';
import '../cubit/job_tracking_cubit.dart';
import '../cubit/job_tracking_state.dart';

/// Ports JobTracking.dc.html's status + completion step. Simplified per
/// the plan's disclosed mismatch: no star rating / quick-tag review
/// system exists in the backend (CompletionCreate only has a free-text
/// client_words field, and nothing links completion to the workers app's
/// references/standing) — this is a single review text field, not a fake
/// star-and-tags UI that would verify nothing real.
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
  final _reviewController = TextEditingController();

  @override
  void dispose() {
    _whatWasDoneController.dispose();
    _reviewController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.job.trade)),
      body: BlocConsumer<JobTrackingCubit, JobTrackingState>(
        listener: (context, state) {
          if (!mounted) return; // Engineering Standard: Async Gap Safety

          if (state is JobTrackingSuccess) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Job confirmed done.')),
            );
            Navigator.of(context).popUntil((route) => route.isFirst);
          } else if (state is JobTrackingFailure) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.errorMessage), backgroundColor: Colors.red),
            );
          }
        },
        builder: (context, state) {
          final isSubmitting = state is JobTrackingSubmitting;
          final canComplete = widget.job.status == 'IN_PROGRESS';

          return Padding(
            padding: const EdgeInsets.all(20),
            child: ListView(
              children: [
                Text('Status: ${widget.job.status}', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                Text('${widget.job.suburb} · ${widget.job.address}'),
                const SizedBox(height: 24),
                if (!canComplete)
                  Text(
                    widget.job.status == 'COMPLETED'
                        ? 'This job is already complete.'
                        : 'This job isn\'t ready to confirm yet (needs to be IN_PROGRESS).',
                  )
                else ...[
                  TextField(
                    controller: _whatWasDoneController,
                    enabled: !isSubmitting,
                    maxLines: 3,
                    decoration: const InputDecoration(labelText: 'What was done?'),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _reviewController,
                    enabled: !isSubmitting,
                    maxLines: 3,
                    decoration: const InputDecoration(labelText: 'A few words about the worker (optional)'),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: isSubmitting ? null : () => _confirm(context),
                    child: isSubmitting
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Confirm job done'),
                  ),
                ],
              ],
            ),
          );
        },
      ),
    );
  }

  void _confirm(BuildContext context) {
    final whatWasDone = _whatWasDoneController.text.trim();
    if (whatWasDone.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Describe what was done to confirm')),
      );
      return;
    }

    final review = _reviewController.text.trim();
    context.read<JobTrackingCubit>().completeJob(
          jobId: widget.job.id,
          whatWasDone: whatWasDone,
          clientWords: review.isEmpty ? null : review,
        );
  }
}
