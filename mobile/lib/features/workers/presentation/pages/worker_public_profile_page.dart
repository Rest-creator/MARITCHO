import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/core/theme/app_theme.dart';
import 'package:mobile/features/workers/data/models/worker_directory_item.dart';
import 'package:mobile/features/workers/data/repositories/workers_repository.dart';
import 'package:mobile/features/workers/presentation/cubit/worker_profile_cubit.dart';
import 'package:mobile/features/workers/presentation/cubit/worker_profile_state.dart';

class WorkerPublicProfilePage extends StatelessWidget {
  final String workerId;

  const WorkerPublicProfilePage({super.key, required this.workerId});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) => WorkerProfileCubit(
        workersRepository: ctx.read<WorkersRepository>(),
        workerId: workerId,
      )..loadProfile(),
      child: const _WorkerPublicProfileView(),
    );
  }
}

class _WorkerPublicProfileView extends StatelessWidget {
  const _WorkerPublicProfileView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Worker Profile')),
      body: BlocBuilder<WorkerProfileCubit, WorkerProfileState>(
        builder: (context, state) {
          if (state is WorkerProfileLoading || state is WorkerProfileInitial) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is WorkerProfileFailure) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text('Failed to load profile: ${state.errorMessage}'),
                  const SizedBox(height: 12),
                  ElevatedButton(
                    onPressed: () =>
                        context.read<WorkerProfileCubit>().loadProfile(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          final profile = (state as WorkerProfileLoaded).profile;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _buildHeader(profile),
              const SizedBox(height: 16),
              _buildStatsCard(profile),
              const SizedBox(height: 16),
              _buildSkillsCard(profile),
              const SizedBox(height: 16),
              _buildCoverageCard(profile),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  style: FilledButton.styleFrom(
                    backgroundColor: AppTheme.primaryBlueGray,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                  icon: const Icon(Icons.add_task),
                  label: const Text(
                    'Hire This Worker (Post Job)',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  onPressed: () {
                    final primaryTrade = profile.trades.isNotEmpty
                        ? profile.trades.first
                        : null;
                    Navigator.of(context)
                        .pushNamed('/post-job', arguments: primaryTrade);
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildHeader(WorkerPublicProfile profile) {
    return Center(
      child: Column(
        children: [
          CircleAvatar(
            radius: 36,
            backgroundColor: AppTheme.primaryBlueGray,
            child: Text(
              profile.name.isNotEmpty ? profile.name[0].toUpperCase() : 'W',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            profile.name,
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: AppTheme.primaryBlueGray.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  profile.grade,
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppTheme.primaryBlueGray,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              if (profile.hasPoliceClearance) ...[
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.green.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: const [
                      Icon(Icons.verified, size: 14, color: Colors.green),
                      SizedBox(width: 4),
                      Text(
                        'Police Cleared',
                        style: TextStyle(fontSize: 11, color: Colors.green),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatsCard(WorkerPublicProfile profile) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: AppTheme.lightBlueGray.withValues(alpha: 0.4)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _statItem('${(profile.onTimeRate * 100).toInt()}%', 'On-Time'),
            _statItem(profile.jobsCompleted.toString(), 'Completed'),
            _statItem(
              profile.ratingAverage != null
                  ? profile.ratingAverage!.toStringAsFixed(1)
                  : 'N/A',
              'Rating',
            ),
          ],
        ),
      ),
    );
  }

  Widget _statItem(String value, String label) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
        ),
      ],
    );
  }

  Widget _buildSkillsCard(WorkerPublicProfile profile) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: AppTheme.lightBlueGray.withValues(alpha: 0.4)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Skills & Trades',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: profile.trades
                  .map(
                    (trade) => Chip(
                      label: Text(trade),
                      backgroundColor: AppTheme.lightBlueGray.withValues(
                        alpha: 0.3,
                      ),
                    ),
                  )
                  .toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCoverageCard(WorkerPublicProfile profile) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: AppTheme.lightBlueGray.withValues(alpha: 0.4)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Location & Travel Reach',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            if (profile.suburb != null)
              Row(
                children: [
                  const Icon(Icons.home_outlined, size: 18, color: Colors.grey),
                  const SizedBox(width: 8),
                  Text('Home: ${profile.suburb}'),
                ],
              ),
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(
                  Icons.directions_car_outlined,
                  size: 18,
                  color: Colors.grey,
                ),
                const SizedBox(width: 8),
                Text('Travel radius: up to ${profile.travelKm} km'),
              ],
            ),
            if (profile.serviceAreas.isNotEmpty) ...[
              const SizedBox(height: 8),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.pin_drop_outlined,
                    size: 18,
                    color: Colors.grey,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Service suburbs: ${profile.serviceAreas.join(", ")}',
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
