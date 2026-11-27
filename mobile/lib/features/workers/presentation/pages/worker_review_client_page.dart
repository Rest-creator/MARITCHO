import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/core/theme/app_theme.dart';
import 'package:mobile/features/jobs/data/models/job.dart';
import 'package:mobile/features/jobs/data/repositories/jobs_repository.dart';
import 'package:mobile/features/jobs/presentation/widgets/review_panel.dart';

class WorkerReviewClientPage extends StatefulWidget {
  final Job job;

  const WorkerReviewClientPage({super.key, required this.job});

  @override
  State<WorkerReviewClientPage> createState() => _WorkerReviewClientPageState();
}

class _WorkerReviewClientPageState extends State<WorkerReviewClientPage> {
  final _commentController = TextEditingController();
  final ReviewDraft _draft = ReviewDraft();
  bool _isSubmitting = false;

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Rate Client')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            widget.job.trade,
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          Text(
            'Location: ${widget.job.suburb}',
            style: TextStyle(color: Colors.grey.shade700),
          ),
          const SizedBox(height: 16),
          ReviewPanel(
            draft: _draft,
            isWorkerReviewingEmployer: true,
            onChanged: (updated) => setState(() {}),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _commentController,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: 'Additional comment (Optional)',
              hintText: 'Share feedback on the job experience...',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: AppTheme.primaryBlueGray,
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
              onPressed: _isSubmitting ? null : _submitReview,
              child: _isSubmitting
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Text(
                      'Submit Double-Blind Review',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _submitReview() async {
    setState(() => _isSubmitting = true);
    final repo = context.read<JobsRepository>();
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);

    final result = await repo.submitReview(
      jobId: widget.job.id,
      rating: _draft.rating,
      tags: _draft.tags,
      comment: _commentController.text.trim().isNotEmpty
          ? _commentController.text.trim()
          : null,
    );

    if (!mounted) return;
    setState(() => _isSubmitting = false);

    result.match(
      onOk: (_) {
        messenger.showSnackBar(
          const SnackBar(
            content: Text(
              'Review submitted! It will appear when the client reviews or after 14 days.',
            ),
          ),
        );
        navigator.pop();
      },
      onError: (failure) {
        messenger.showSnackBar(
          SnackBar(content: Text(failure.message), backgroundColor: Colors.red),
        );
      },
    );
  }
}
