import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/brand_logo.dart';
import '../../data/models/open_job.dart';
import '../../data/repositories/jobs_repository.dart';
import '../cubit/worker_home_cubit.dart';
import '../cubit/worker_home_state.dart';

/// Redesigned Worker Home Page matching `frontend/src/features/worker/WorkerHomeScreen.tsx`:
/// - Brand Header with BrandLogo and Status Pill
/// - Open jobs list with styled glass cards, distance badges, budget indicator, and time tags
class WorkerHomePage extends StatelessWidget {
  const WorkerHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) =>
          WorkerHomeCubit(ctx.read<JobsRepository>())..loadOpenJobs(),
      child: const _WorkerHomeView(),
    );
  }
}

class _WorkerHomeView extends StatelessWidget {
  const _WorkerHomeView();

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      color: AppTheme.cyanAccent,
      backgroundColor: AppTheme.brandNavy,
      onRefresh: () => context.read<WorkerHomeCubit>().loadOpenJobs(),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 100),
        children: [
          // Header Bar
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const BrandLogo(markSize: 24, fontSize: 18),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: AppTheme.emeraldTint,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppTheme.emeraldEdge),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.circle, size: 8, color: AppTheme.emeraldAccent),
                    SizedBox(width: 6),
                    Text(
                      'Ready for work',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.emeraldAccent,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Title & Subtitle
          const Text(
            'Jobs near you',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              color: AppTheme.text,
              letterSpacing: -0.4,
            ),
          ),
          const SizedBox(height: 4),
          const Text(
            'New opportunities in your area needing skilled hands',
            style: TextStyle(fontSize: 14, color: AppTheme.textSecondary),
          ),
          const SizedBox(height: 20),

          BlocBuilder<WorkerHomeCubit, WorkerHomeState>(
            builder: (context, state) {
              if (state is WorkerHomeInitial || state is WorkerHomeLoading) {
                return const Center(
                  child: Padding(
                    padding: EdgeInsets.all(32),
                    child: CircularProgressIndicator(
                      color: AppTheme.cyanAccent,
                    ),
                  ),
                );
              }
              if (state is WorkerHomeFailure) {
                return Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.dangerTint,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppTheme.dangerEdge),
                  ),
                  child: Text(
                    'Could not load jobs: ${state.errorMessage}',
                    style: const TextStyle(color: AppTheme.textSecondary),
                  ),
                );
              }
              final jobs = (state as WorkerHomeLoaded).jobs;
              if (jobs.isEmpty) {
                return Container(
                  padding: const EdgeInsets.all(32),
                  decoration: BoxDecoration(
                    color: AppTheme.glass,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppTheme.lineSubtle),
                  ),
                  child: const Center(
                    child: Text(
                      'No open jobs near you right now.\nPull down to refresh.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: AppTheme.textSecondary,
                        fontSize: 14,
                        height: 1.4,
                      ),
                    ),
                  ),
                );
              }
              return Column(
                children: [for (final job in jobs) _OpenJobCard(job: job)],
              );
            },
          ),
        ],
      ),
    );
  }
}

class _OpenJobCard extends StatelessWidget {
  final OpenJob job;

  const _OpenJobCard({required this.job});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      decoration: BoxDecoration(
        color: AppTheme.glassStrong,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.line),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(18),
          onTap: () =>
              Navigator.of(context).pushNamed('/job-detail', arguments: job),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: AppTheme.cyanTintSoft,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppTheme.cyanEdge),
                      ),
                      child: Text(
                        job.trade,
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.cyanAccent,
                        ),
                      ),
                    ),
                    Text(
                      '\$${job.budgetAmount}',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.text,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  job.problemDescription ?? 'No description provided',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 14,
                    color: AppTheme.textSecondary,
                    height: 1.35,
                  ),
                ),
                const SizedBox(height: 14),
                Row(
                  children: [
                    const Icon(
                      Icons.location_on_outlined,
                      size: 15,
                      color: AppTheme.textMuted,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      job.suburb,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppTheme.textMuted,
                      ),
                    ),
                    const Spacer(),
                    const Text(
                      'View details',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.cyanAccent,
                      ),
                    ),
                    const SizedBox(width: 2),
                    const Icon(
                      Icons.chevron_right,
                      size: 16,
                      color: AppTheme.cyanAccent,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
