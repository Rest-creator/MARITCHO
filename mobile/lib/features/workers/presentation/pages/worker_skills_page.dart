import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/error/result.dart';
import '../../../suburbs/data/models/suburb.dart';
import '../../../suburbs/data/repositories/suburbs_repository.dart';
import '../../data/repositories/workers_repository.dart';
import '../cubit/worker_skills_cubit.dart';
import '../cubit/worker_skills_state.dart';

const _trades = [
  ('Plumber', 'PLUMBING'),
  ('Electrician', 'ELECTRICAL'),
  ('Solar', 'SOLAR'),
  ('Welder', 'WELDING'),
  ('Builder', 'BUILDING'),
  ('Appliance repair', 'APPLIANCE_REPAIR'),
];

const _maxTrades = 5;

/// Ports the wireframe's "Step 2/2" worker onboarding: trade multi-select
/// (up to 5) and one service area (suburb + travel means). The
/// wireframe's travel-distance slider and portfolio-photo upload are
/// dropped: service areas are a list of specific suburbs, not a
/// radius-from-home-suburb concept, and no photo-upload storage exists
/// anywhere in this backend yet.
class WorkerSkillsPage extends StatefulWidget {
  const WorkerSkillsPage({super.key});

  @override
  State<WorkerSkillsPage> createState() => _WorkerSkillsPageState();
}

class _WorkerSkillsPageState extends State<WorkerSkillsPage> {
  late final Future<Result<List<Suburb>, Failure>> _suburbsFuture;
  final _selectedTrades = <String>{};
  String? _suburb;
  final _travelMeansController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _suburbsFuture = context.read<SuburbsRepository>().listSuburbs();
  }

  @override
  void dispose() {
    _travelMeansController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) => WorkerSkillsCubit(ctx.read<WorkersRepository>()),
      child: Scaffold(
        appBar: AppBar(title: const Text('What work can you do?')),
        body: BlocConsumer<WorkerSkillsCubit, WorkerSkillsState>(
          listener: (context, state) {
            if (!mounted) return; // Engineering Standard: Async Gap Safety

            if (state is WorkerSkillsSuccess) {
              Navigator.of(context).pushReplacementNamed('/worker-home');
            } else if (state is WorkerSkillsFailure) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text(state.errorMessage), backgroundColor: Colors.red),
              );
            }
          },
          builder: (context, state) {
            final isSubmitting = state is WorkerSkillsSubmitting;

            return FutureBuilder<Result<List<Suburb>, Failure>>(
              future: _suburbsFuture,
              builder: (context, snapshot) {
                if (!snapshot.hasData) {
                  return const Center(child: CircularProgressIndicator());
                }
                final result = snapshot.data!;
                if (result.isError) {
                  return Center(child: Text('Could not load suburbs: ${result.errorValue.message}'));
                }
                final suburbs = result.okValue;

                return Padding(
                  padding: const EdgeInsets.all(20),
                  child: ListView(
                    children: [
                      Text('Pick up to $_maxTrades. What you can do matters more than certificates.'),
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          for (final (label, value) in _trades)
                            FilterChip(
                              label: Text(label),
                              selected: _selectedTrades.contains(value),
                              onSelected: isSubmitting
                                  ? null
                                  : (selected) => setState(() {
                                        if (selected) {
                                          if (_selectedTrades.length < _maxTrades) {
                                            _selectedTrades.add(value);
                                          }
                                        } else {
                                          _selectedTrades.remove(value);
                                        }
                                      }),
                            ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      DropdownButtonFormField<String>(
                        initialValue: _suburb,
                        decoration: const InputDecoration(labelText: 'Where do you work from?'),
                        items: [
                          for (final suburb in suburbs)
                            DropdownMenuItem(value: suburb.name, child: Text(suburb.name)),
                        ],
                        onChanged: isSubmitting ? null : (value) => setState(() => _suburb = value),
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _travelMeansController,
                        enabled: !isSubmitting,
                        decoration: const InputDecoration(labelText: 'How do you get around? (optional)'),
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
                            : const Text('Start finding work'),
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
    if (_selectedTrades.isEmpty || _suburb == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Pick at least one trade and your suburb to continue')),
      );
      return;
    }

    final travelMeans = _travelMeansController.text.trim();
    context.read<WorkerSkillsCubit>().submit(
          trades: _selectedTrades.toList(),
          suburb: _suburb!,
          travelMeans: travelMeans.isEmpty ? null : travelMeans,
        );
  }
}
