import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/models/open_job.dart';
import '../../data/repositories/jobs_repository.dart';
import '../cubit/worker_home_cubit.dart';
import '../cubit/worker_home_state.dart';

/// Ports WorkerHome.dc.html's job feed. The wireframe's availability
/// toggle is omitted: no is_available/presence concept exists anywhere
/// on the backend, and an interactive-looking switch that does nothing
/// would be dishonest UI.
class WorkerHomePage extends StatelessWidget {
  const WorkerHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) => WorkerHomeCubit(ctx.read<JobsRepository>())..loadOpenJobs(),
      child: const _WorkerHomeView(),
    );
  }
}

class _WorkerHomeView extends StatelessWidget {
  const _WorkerHomeView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Jobs near you'),
        actions: [
          IconButton(
            icon: const Icon(Icons.work_history),
            tooltip: 'My work',
            onPressed: () => Navigator.of(context).pushNamed('/my-work'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => context.read<WorkerHomeCubit>().loadOpenJobs(),
        child: BlocBuilder<WorkerHomeCubit, WorkerHomeState>(
          builder: (context, state) {
            if (state is WorkerHomeInitial || state is WorkerHomeLoading) {
              return const Center(child: CircularProgressIndicator());
            }
            if (state is WorkerHomeFailure) {
              return Center(child: Text('Could not load jobs: ${state.errorMessage}'));
            }
            final jobs = (state as WorkerHomeLoaded).jobs;
            if (jobs.isEmpty) {
              return const Center(child: Text('No open jobs near you right now.'));
            }
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [for (final job in jobs) _OpenJobCard(job: job)],
            );
          },
        ),
      ),
    );
  }
}

class _OpenJobCard extends StatelessWidget {
  final OpenJob job;

  const _OpenJobCard({required this.job});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        title: Text(job.trade),
        subtitle: Text(
          '${job.suburb} · ${job.distanceKm.toStringAsFixed(1)}km · ${job.distanceBand}',
        ),
        trailing: job.budgetAmount != null ? Text('\$${job.budgetAmount!.toStringAsFixed(2)}') : null,
        onTap: () => Navigator.of(context).pushNamed('/job-detail', arguments: job),
      ),
    );
  }
}
