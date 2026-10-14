import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/error/result.dart';
import '../../../suburbs/data/models/suburb.dart';
import '../../../suburbs/data/repositories/suburbs_repository.dart';
import '../../data/repositories/jobs_repository.dart';
import '../cubit/post_job_cubit.dart';
import '../cubit/post_job_state.dart';

const _trades = [
  ('Plumber', 'PLUMBING'),
  ('Electrician', 'ELECTRICAL'),
  ('Solar', 'SOLAR'),
  ('Welder', 'WELDING'),
  ('Builder', 'BUILDING'),
  ('Appliance repair', 'APPLIANCE_REPAIR'),
];

/// Ports PostJob.dc.html's form. The suburb list is fetched once (plain
/// FutureBuilder, not a Cubit — a one-shot read with no further state of
/// its own doesn't need one) to populate a dropdown instead of free text,
/// matching the suburbs endpoint's own documented purpose.
class PostJobPage extends StatefulWidget {
  final String? initialTrade;

  const PostJobPage({super.key, this.initialTrade});

  @override
  State<PostJobPage> createState() => _PostJobPageState();
}

class _PostJobPageState extends State<PostJobPage> {
  late final Future<Result<List<Suburb>, Failure>> _suburbsFuture;
  final _addressController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _budgetController = TextEditingController();

  String? _trade;
  String? _suburb;

  @override
  void initState() {
    super.initState();
    _trade = widget.initialTrade;
    _suburbsFuture = context.read<SuburbsRepository>().listSuburbs();
  }

  @override
  void dispose() {
    _addressController.dispose();
    _descriptionController.dispose();
    _budgetController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) => PostJobCubit(ctx.read<JobsRepository>()),
      child: Scaffold(
        appBar: AppBar(title: const Text('Post a job')),
        body: BlocConsumer<PostJobCubit, PostJobState>(
          listener: (context, state) {
            if (!mounted) return; // Engineering Standard: Async Gap Safety

            if (state is PostJobSuccess) {
              Navigator.of(context)
                  .pushReplacementNamed('/applicants', arguments: state.job.id);
            } else if (state is PostJobFailure) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(state.errorMessage),
                  backgroundColor: Colors.red,
                ),
              );
            }
          },
          builder: (context, state) {
            final isSubmitting = state is PostJobSubmitting;
            return FutureBuilder<Result<List<Suburb>, Failure>>(
              future: _suburbsFuture,
              builder: (context, snapshot) {
                if (!snapshot.hasData) {
                  return const Center(child: CircularProgressIndicator());
                }
                final result = snapshot.data!;
                if (result.isError) {
                  return Center(
                    child: Text(
                      'Could not load suburbs: ${result.errorValue.message}',
                    ),
                  );
                }
                final suburbs = result.okValue;

                return Padding(
                  padding: const EdgeInsets.all(20),
                  child: ListView(
                    children: [
                      DropdownButtonFormField<String>(
                        initialValue: _trade,
                        decoration: const InputDecoration(
                          labelText: 'What needs doing?',
                        ),
                        items: [
                          for (final (label, value) in _trades)
                            DropdownMenuItem(value: value, child: Text(label)),
                        ],
                        onChanged: isSubmitting
                            ? null
                            : (value) => setState(() => _trade = value),
                      ),
                      const SizedBox(height: 16),
                      DropdownButtonFormField<String>(
                        initialValue: _suburb,
                        decoration: const InputDecoration(labelText: 'Suburb'),
                        items: [
                          for (final suburb in suburbs)
                            DropdownMenuItem(
                              value: suburb.name,
                              child: Text(suburb.name),
                            ),
                        ],
                        onChanged: isSubmitting
                            ? null
                            : (value) => setState(() => _suburb = value),
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _addressController,
                        enabled: !isSubmitting,
                        decoration: const InputDecoration(
                          labelText: 'Exact address',
                        ),
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _descriptionController,
                        enabled: !isSubmitting,
                        maxLines: 4,
                        decoration: const InputDecoration(
                          labelText: 'Describe the job',
                        ),
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _budgetController,
                        enabled: !isSubmitting,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: const InputDecoration(
                          labelText: 'Your budget (optional)',
                          prefixText: 'US\$ ',
                        ),
                      ),
                      const SizedBox(height: 24),
                      ElevatedButton(
                        onPressed: isSubmitting ? null : () => _submit(context),
                        child: isSubmitting
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Text('Find someone for this job'),
                      ),
                    ],
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }

  void _submit(BuildContext context) {
    if (_trade == null ||
        _suburb == null ||
        _addressController.text.trim().isEmpty ||
        _descriptionController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Fill in the trade, suburb, address and description to continue',
          ),
        ),
      );
      return;
    }

    final budgetText = _budgetController.text.trim();
    context.read<PostJobCubit>().submit(
      trade: _trade!,
      suburb: _suburb!,
      address: _addressController.text.trim(),
      problemDescription: _descriptionController.text.trim(),
      budgetAmount: budgetText.isEmpty ? null : double.tryParse(budgetText),
    );
  }
}
