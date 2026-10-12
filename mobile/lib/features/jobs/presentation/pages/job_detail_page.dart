import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/models/open_job.dart';
import '../../data/repositories/jobs_repository.dart';
import '../cubit/job_detail_cubit.dart';
import '../cubit/job_detail_state.dart';

/// Ports JobDetail.dc.html. Renders from the OpenJob already fetched for
/// WorkerHome's list — no GET /jobs/{id} call, since a worker isn't a
/// party to an unbooked job (the backend would 403 them) and the open-
/// jobs feed already has everything needed to render this screen.
class JobDetailPage extends StatefulWidget {
  final OpenJob job;

  const JobDetailPage({super.key, required this.job});

  @override
  State<JobDetailPage> createState() => _JobDetailPageState();
}

class _JobDetailPageState extends State<JobDetailPage> {
  final _priceController = TextEditingController();
  final _availabilityController = TextEditingController();

  @override
  void dispose() {
    _priceController.dispose();
    _availabilityController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) => JobDetailCubit(ctx.read<JobsRepository>()),
      child: Scaffold(
        appBar: AppBar(title: Text(widget.job.trade)),
        body: BlocConsumer<JobDetailCubit, JobDetailState>(
          listener: (context, state) {
            if (!mounted) return; // Engineering Standard: Async Gap Safety

            if (state is JobDetailSuccess) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Offer sent.')),
              );
              Navigator.of(context).pushReplacementNamed('/my-work');
            } else if (state is JobDetailFailure) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text(state.errorMessage), backgroundColor: Colors.red),
              );
            }
          },
          builder: (context, state) {
            final isSubmitting = state is JobDetailSubmitting;

            return Padding(
              padding: const EdgeInsets.all(20),
              child: ListView(
                children: [
                  Text('What the client needs', style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 8),
                  Text(widget.job.problemDescription ?? 'No description provided.'),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _MetaColumn(label: 'Where', value: widget.job.suburb),
                      _MetaColumn(
                        label: 'Distance',
                        value: '${widget.job.distanceKm.toStringAsFixed(1)}km',
                      ),
                      _MetaColumn(
                        label: 'Budget',
                        value: widget.job.budgetAmount != null
                            ? '\$${widget.job.budgetAmount!.toStringAsFixed(2)}'
                            : 'Not set',
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  Text('Your offer', style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _priceController,
                    enabled: !isSubmitting,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(labelText: 'Your price', prefixText: 'US\$ '),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _availabilityController,
                    enabled: !isSubmitting,
                    decoration: const InputDecoration(labelText: 'When can you come? (optional)'),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: isSubmitting ? null : () => _submit(context),
                    child: isSubmitting
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Send my offer'),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  void _submit(BuildContext context) {
    final price = double.tryParse(_priceController.text.trim());
    if (price == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter a valid price to continue')),
      );
      return;
    }

    final availability = _availabilityController.text.trim();
    context.read<JobDetailCubit>().submitOffer(
          jobId: widget.job.jobId,
          quotedAmount: price,
          availabilityNote: availability.isEmpty ? null : availability,
        );
  }
}

class _MetaColumn extends StatelessWidget {
  final String label;
  final String value;

  const _MetaColumn({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
      ],
    );
  }
}
