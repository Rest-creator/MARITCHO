import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/theme/app_theme.dart';
import '../../data/models/match_candidate.dart';
import '../../data/repositories/jobs_repository.dart';
import '../cubit/applicants_cubit.dart';
import '../cubit/applicants_state.dart';

/// Ports Applicants.dc.html: ranked candidates, each showing its own
/// JobOffer (price/availability) when the worker has submitted one, a
/// manual deposit-amount prompt otherwise (the backend never requires
/// deposit_amount to equal quoted_amount).
class ApplicantsPage extends StatelessWidget {
  final String jobId;

  const ApplicantsPage({super.key, required this.jobId});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) => ApplicantsCubit(ctx.read<JobsRepository>())..loadMatches(jobId),
      child: _ApplicantsView(jobId: jobId),
    );
  }
}

class _ApplicantsView extends StatelessWidget {
  final String jobId;

  const _ApplicantsView({required this.jobId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Applicants')),
      body: BlocConsumer<ApplicantsCubit, ApplicantsState>(
        listener: (context, state) {
          if (!context.mounted) return; // Engineering Standard: Async Gap Safety

          if (state is ApplicantsBooked) {
            Navigator.of(context).pushReplacementNamed('/job-tracking', arguments: state.job);
          } else if (state is ApplicantsFailure) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.errorMessage), backgroundColor: Colors.red),
            );
          }
        },
        builder: (context, state) {
          if (state is ApplicantsInitial || state is ApplicantsLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          final candidates = switch (state) {
            ApplicantsLoaded(:final candidates) => candidates,
            ApplicantsBooking(:final candidates) => candidates,
            _ => const <MatchCandidate>[],
          };
          final isBooking = state is ApplicantsBooking;

          if (candidates.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text('No matching workers yet — check back soon.'),
              ),
            );
          }

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              for (final candidate in candidates)
                _CandidateCard(
                  candidate: candidate,
                  isBooking: isBooking,
                  onHire: () => _promptAndHire(context, candidate),
                ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _promptAndHire(BuildContext context, MatchCandidate candidate) async {
    final controller = TextEditingController(
      text: candidate.quotedAmount?.toStringAsFixed(2) ?? '',
    );

    final depositAmount = await showDialog<double>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Deposit amount'),
        content: TextField(
          controller: controller,
          autofocus: true,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(prefixText: 'US\$ '),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(double.tryParse(controller.text)),
            child: const Text('Hire'),
          ),
        ],
      ),
    );

    if (depositAmount == null || !context.mounted) return;

    context.read<ApplicantsCubit>().hireWorker(
          jobId: jobId,
          workerId: candidate.workerId,
          depositAmount: depositAmount,
        );
  }
}

class _CandidateCard extends StatelessWidget {
  final MatchCandidate candidate;
  final bool isBooking;
  final VoidCallback onHire;

  const _CandidateCard({required this.candidate, required this.isBooking, required this.onHire});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(backgroundColor: AppTheme.lightBlueGray, child: Text(candidate.grade.substring(0, 1))),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('${candidate.grade} · ${candidate.distanceBand}', style: const TextStyle(fontWeight: FontWeight.bold)),
                      Text('${candidate.suburb} · ${candidate.distanceKm.toStringAsFixed(1)}km'),
                    ],
                  ),
                ),
                if (candidate.quotedAmount != null)
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text('\$${candidate.quotedAmount!.toStringAsFixed(2)}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      const Text('quote', style: TextStyle(fontSize: 11)),
                    ],
                  ),
              ],
            ),
            const SizedBox(height: 8),
            Text(candidate.reason, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontSize: 12)),
            if (candidate.availabilityNote != null) ...[
              const SizedBox(height: 6),
              Text(candidate.availabilityNote!, style: const TextStyle(fontStyle: FontStyle.italic, fontSize: 12)),
            ],
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: isBooking ? null : onHire,
                child: Text('Hire'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
