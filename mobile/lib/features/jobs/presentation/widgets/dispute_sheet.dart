import 'package:flutter/material.dart';

import 'package:mobile/features/jobs/data/repositories/jobs_repository.dart';

class DisputeSheet extends StatefulWidget {
  final String jobId;
  final JobsRepository jobsRepository;
  final VoidCallback onDisputeRaised;

  const DisputeSheet({
    super.key,
    required this.jobId,
    required this.jobsRepository,
    required this.onDisputeRaised,
  });

  static Future<void> show(
    BuildContext context, {
    required String jobId,
    required JobsRepository jobsRepository,
    required VoidCallback onDisputeRaised,
  }) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => DisputeSheet(
        jobId: jobId,
        jobsRepository: jobsRepository,
        onDisputeRaised: onDisputeRaised,
      ),
    );
  }

  @override
  State<DisputeSheet> createState() => _DisputeSheetState();
}

class _DisputeSheetState extends State<DisputeSheet> {
  final _reasonController = TextEditingController();
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    _reasonController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;

    return Container(
      padding: EdgeInsets.fromLTRB(20, 20, 20, 20 + bottomInset),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.warning_amber_rounded, color: Colors.amber),
              const SizedBox(width: 8),
              const Text(
                "Something's not right?",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.of(context).pop(),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            "Raising a concern freezes payment immediately until the worker responds or conducts a return visit.",
            style: TextStyle(color: Colors.black54, fontSize: 13),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _reasonController,
            maxLines: 4,
            decoration: const InputDecoration(
              hintText: "Describe what went wrong or needs attention...",
              border: OutlineInputBorder(),
            ),
          ),
          if (_errorMessage != null) ...[
            const SizedBox(height: 8),
            Text(
              _errorMessage!,
              style: const TextStyle(color: Colors.red, fontSize: 12),
            ),
          ],
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: Colors.red.shade700,
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
              onPressed: _isSubmitting ? null : _submitDispute,
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
                      'Freeze Payment & Report Issue',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _submitDispute() async {
    final text = _reasonController.text.trim();
    if (text.isEmpty) {
      setState(() => _errorMessage = 'Please describe the issue.');
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    final result = await widget.jobsRepository.raiseDispute(
      jobId: widget.jobId,
      reason: text,
    );

    if (!mounted) return;

    result.match(
      onOk: (_) {
        Navigator.of(context).pop();
        widget.onDisputeRaised();
      },
      onError: (failure) {
        setState(() {
          _isSubmitting = false;
          _errorMessage = failure.message;
        });
      },
    );
  }
}
