import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../jobs/data/models/job.dart';
import '../../../jobs/data/models/my_offer.dart';
import '../../../jobs/data/repositories/jobs_repository.dart';
import '../../data/repositories/workers_repository.dart';
import '../cubit/my_work_cubit.dart';
import '../cubit/my_work_state.dart';

/// Ports MyWork.dc.html. The stats header shows Jobs completed and
/// On-time rate (from GET /workers/me/standing) instead of the
/// wireframe's "$Earned"/star rating — no earnings-aggregate endpoint
/// and no numeric rating exist anywhere in the backend; not faked here.
class MyWorkPage extends StatelessWidget {
  const MyWorkPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) => MyWorkCubit(ctx.read<WorkersRepository>(), ctx.read<JobsRepository>())..load(),
      child: const _MyWorkView(),
    );
  }
}

class _MyWorkView extends StatelessWidget {
  const _MyWorkView();

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('My work'),
          bottom: const TabBar(
            tabs: [Tab(text: 'Offers'), Tab(text: 'Active'), Tab(text: 'Done')],
          ),
        ),
        body: BlocBuilder<MyWorkCubit, MyWorkState>(
          builder: (context, state) {
            if (state is MyWorkInitial || state is MyWorkLoading) {
              return const Center(child: CircularProgressIndicator());
            }
            if (state is MyWorkFailure) {
              return Center(child: Text('Could not load your work: ${state.errorMessage}'));
            }

            final loaded = state as MyWorkLoaded;
            return Column(
              children: [
                _StatsRow(loaded: loaded),
                Expanded(
                  child: TabBarView(
                    children: [
                      _OffersTab(offers: loaded.offers),
                      _JobsTab(jobs: loaded.activeJobs, emptyText: 'No active jobs.'),
                      _JobsTab(jobs: loaded.doneJobs, emptyText: 'No completed jobs yet.'),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _StatsRow extends StatelessWidget {
  final MyWorkLoaded loaded;

  const _StatsRow({required this.loaded});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _Stat(value: '${loaded.standing.jobsCompleted}', label: 'Jobs completed'),
          _Stat(value: '${loaded.standing.onTimeRate.toStringAsFixed(0)}%', label: 'On-time rate'),
          _Stat(value: loaded.standing.grade, label: 'Grade'),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final String value;
  final String label;

  const _Stat({required this.value, required this.label});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
      ],
    );
  }
}

class _OffersTab extends StatelessWidget {
  final List<MyOffer> offers;

  const _OffersTab({required this.offers});

  @override
  Widget build(BuildContext context) {
    if (offers.isEmpty) {
      return const Center(child: Text('No offers submitted yet.'));
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        for (final offer in offers)
          Card(
            margin: const EdgeInsets.only(bottom: 10),
            child: ListTile(
              title: Text(offer.jobTrade),
              subtitle: Text('${offer.jobSuburb} · ${offer.jobStatus}'),
              trailing: Text('\$${offer.quotedAmount.toStringAsFixed(2)}'),
            ),
          ),
      ],
    );
  }
}

class _JobsTab extends StatelessWidget {
  final List<Job> jobs;
  final String emptyText;

  const _JobsTab({required this.jobs, required this.emptyText});

  @override
  Widget build(BuildContext context) {
    if (jobs.isEmpty) {
      return Center(child: Text(emptyText));
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        for (final job in jobs)
          Card(
            margin: const EdgeInsets.only(bottom: 10),
            child: ListTile(
              title: Text(job.trade),
              subtitle: Text('${job.suburb} · ${job.status}'),
            ),
          ),
      ],
    );
  }
}
