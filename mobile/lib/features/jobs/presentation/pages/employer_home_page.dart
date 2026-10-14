import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/theme/app_theme.dart';
import '../../data/models/job.dart';
import '../../data/repositories/jobs_repository.dart';
import '../cubit/employer_home_cubit.dart';
import '../cubit/employer_home_state.dart';

/// Ports EmployerHome.dc.html's "What needs doing?" search card, popular
/// trades grid (unselected — trade preselection is a follow-up), and
/// "Your jobs" list (offer-count badge, tap routes to Applicants or Job
/// Tracking depending on status).
class EmployerHomePage extends StatelessWidget {
  const EmployerHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) =>
          EmployerHomeCubit(ctx.read<JobsRepository>())..loadJobs(),
      child: const _EmployerHomeView(),
    );
  }
}

class _EmployerHomeView extends StatelessWidget {
  const _EmployerHomeView();

  static const _trades = [
    ('Plumber', Icons.plumbing, 'PLUMBING'),
    ('Electrician', Icons.bolt, 'ELECTRICAL'),
    ('Solar', Icons.solar_power, 'SOLAR'),
    ('Welder', Icons.construction, 'WELDING'),
    ('Builder', Icons.foundation, 'BUILDING'),
    ('Appliance repair', Icons.handyman, 'APPLIANCE_REPAIR'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Maricho')),
      body: RefreshIndicator(
        onRefresh: () => context.read<EmployerHomeCubit>().loadJobs(),
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Card(
              child: ListTile(
                leading: const Icon(
                  Icons.search,
                  color: AppTheme.primaryBlueGray,
                ),
                title: const Text(
                  'What needs doing?',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                subtitle: const Text('A leaking tap, a cut lawn, a driver…'),
                onTap: () => Navigator.of(context).pushNamed('/post-job'),
              ),
            ),
            const SizedBox(height: 20),
            Text(
              'Popular near you',
              style: Theme.of(context).textTheme.bodyMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            GridView.count(
              crossAxisCount: 4,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 10,
              crossAxisSpacing: 10,
              children: [
                for (final (label, icon, trade) in _trades)
                  _TradeTile(
                    label: label,
                    icon: icon,
                    onTap: () =>
                        Navigator.of(context)
                            .pushNamed('/post-job', arguments: trade),
                  ),
              ],
            ),
            const SizedBox(height: 24),
            Text(
              'Your jobs',
              style: Theme.of(context).textTheme.bodyMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            BlocBuilder<EmployerHomeCubit, EmployerHomeState>(
              builder: (context, state) {
                if (state is EmployerHomeLoading ||
                    state is EmployerHomeInitial) {
                  return const Center(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: CircularProgressIndicator(),
                    ),
                  );
                }
                if (state is EmployerHomeFailure) {
                  return Text(
                    'Could not load your jobs: ${state.errorMessage}',
                  );
                }
                final jobs = (state as EmployerHomeLoaded).jobs;
                if (jobs.isEmpty) {
                  return const Text('No jobs posted yet.');
                }
                return Column(
                  children: [for (final job in jobs) _JobCard(job: job)],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _TradeTile extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback onTap;

  const _TradeTile({
    required this.label,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: AppTheme.lightBlueGray.withValues(alpha: 0.3),
          borderRadius: BorderRadius.circular(16),
        ),
        padding: const EdgeInsets.all(8),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: AppTheme.darkBlueGray),
            const SizedBox(height: 6),
            Text(
              label,
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _JobCard extends StatelessWidget {
  final Job job;

  const _JobCard({required this.job});

  @override
  Widget build(BuildContext context) {
    final notBookedYet =
        job.workerId == null &&
        (job.status == 'REQUESTED' || job.status == 'MATCHED');

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        title: Text(job.trade),
        subtitle: Text('${job.suburb} · ${job.status}'),
        trailing: job.offerCount != null && job.offerCount! > 0
            ? Chip(label: Text('${job.offerCount} offers'))
            : null,
        onTap: () {
          if (notBookedYet) {
            Navigator.of(context).pushNamed('/applicants', arguments: job.id);
          } else {
            Navigator.of(context).pushNamed('/job-tracking', arguments: job);
          }
        },
      ),
    );
  }
}
