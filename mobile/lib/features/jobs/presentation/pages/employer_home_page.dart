import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/brand_logo.dart';
import '../../data/models/job.dart';
import '../../data/repositories/jobs_repository.dart';
import '../cubit/employer_home_cubit.dart';
import '../cubit/employer_home_state.dart';

/// Redesigned Employer Home Page matching `frontend/src/features/employer/EmployerHomeScreen.tsx`:
/// - Brand header with BrandLogo & greeting
/// - Hero card ("What needs to be done?") with Sky Cyan search icon
/// - Popular trades grid with two-tone accents (Sky Cyan / Emerald)
/// - "Your jobs" list with glass cards and active offer badges
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
    ('Plumber', Icons.plumbing, 'PLUMBING', AppTheme.cyanAccent),
    ('Electrician', Icons.bolt, 'ELECTRICAL', AppTheme.cyanAccent),
    ('Solar', Icons.solar_power, 'SOLAR', AppTheme.cyanAccent),
    ('Welder', Icons.construction, 'WELDING', AppTheme.emeraldAccent),
    ('Builder', Icons.foundation, 'BUILDING', AppTheme.cyanAccent),
    ('Appliances', Icons.handyman, 'APPLIANCE_REPAIR', AppTheme.emeraldAccent),
  ];

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      color: AppTheme.cyanAccent,
      backgroundColor: AppTheme.brandNavy,
      onRefresh: () => context.read<EmployerHomeCubit>().loadJobs(),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 100),
        children: [
          // Top Header Bar
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const BrandLogo(markSize: 24, fontSize: 18),
              Container(
                decoration: BoxDecoration(
                  color: AppTheme.glass,
                  shape: BoxShape.circle,
                  border: Border.all(color: AppTheme.lineSubtle),
                ),
                child: IconButton(
                  icon: const Icon(
                    Icons.notifications_none,
                    color: AppTheme.textSecondary,
                  ),
                  onPressed: () {},
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Search Hero Card ("What needs to be done?")
          Container(
            decoration: BoxDecoration(
              color: AppTheme.glassStrong,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppTheme.line, width: 1.0),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.15),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                borderRadius: BorderRadius.circular(20),
                onTap: () => Navigator.of(context).pushNamed('/post-job'),
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Row(
                    children: [
                      Container(
                        width: 48,
                        height: 48,
                        decoration: BoxDecoration(
                          color: AppTheme.cyanTintSoft,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(
                            color: AppTheme.cyanAccent.withValues(alpha: 0.4),
                          ),
                        ),
                        child: const Icon(
                          Icons.search,
                          color: AppTheme.cyanAccent,
                          size: 26,
                        ),
                      ),
                      const SizedBox(width: 16),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'What needs to be done?',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w700,
                                color: AppTheme.text,
                              ),
                            ),
                            SizedBox(height: 4),
                            Text(
                              'A leaking tap, a cut lawn, solar repairs…',
                              style: TextStyle(
                                fontSize: 13,
                                color: AppTheme.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Icon(
                        Icons.add_circle,
                        color: AppTheme.cyanAccent,
                        size: 28,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 28),

          // Popular Near You
          const Text(
            'POPULAR NEAR YOU',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: AppTheme.textMuted,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 12),

          GridView.count(
            crossAxisCount: 3,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.15,
            children: [
              for (final (label, icon, trade, accentColor) in _trades)
                _TradeTile(
                  label: label,
                  icon: icon,
                  accentColor: accentColor,
                  onTap: () =>
                      Navigator.of(context)
                          .pushNamed('/post-job', arguments: trade),
                ),
            ],
          ),
          const SizedBox(height: 28),

          // Your Jobs Header
          const Text(
            'YOUR JOBS',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: AppTheme.textMuted,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 12),

          BlocBuilder<EmployerHomeCubit, EmployerHomeState>(
            builder: (context, state) {
              if (state is EmployerHomeInitial ||
                  state is EmployerHomeLoading) {
                return const Center(
                  child: Padding(
                    padding: EdgeInsets.all(32),
                    child: CircularProgressIndicator(
                      color: AppTheme.cyanAccent,
                    ),
                  ),
                );
              }
              if (state is EmployerHomeFailure) {
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
              final jobs = (state as EmployerHomeLoaded).jobs;
              if (jobs.isEmpty) {
                return Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: AppTheme.glass,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppTheme.lineSubtle),
                  ),
                  child: const Center(
                    child: Text(
                      'No jobs posted yet. Tap above to get started.',
                      style: TextStyle(
                        color: AppTheme.textSecondary,
                        fontSize: 14,
                      ),
                    ),
                  ),
                );
              }
              return Column(
                children: [for (final job in jobs) _EmployerJobCard(job: job)],
              );
            },
          ),
        ],
      ),
    );
  }
}

class _TradeTile extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color accentColor;
  final VoidCallback onTap;

  const _TradeTile({
    required this.label,
    required this.icon,
    required this.accentColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppTheme.glassStrong,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.lineSubtle),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: onTap,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: accentColor, size: 28),
              const SizedBox(height: 8),
              Text(
                label,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.text,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmployerJobCard extends StatelessWidget {
  final Job job;

  const _EmployerJobCard({required this.job});

  @override
  Widget build(BuildContext context) {
    final count = job.offerCount ?? 0;
    final hasOffers = count > 0;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppTheme.glassStrong,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.line),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () {
            if (job.status == 'BOOKED') {
              Navigator.of(context).pushNamed('/job-tracking', arguments: job);
            } else {
              Navigator.of(context).pushNamed('/applicants', arguments: job.id);
            }
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        job.trade,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.text,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        job.problemDescription ?? 'No description provided',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 13,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                if (hasOffers)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: AppTheme.cyanTintSoft,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: AppTheme.cyanAccent.withValues(alpha: 0.5),
                      ),
                    ),
                    child: Text(
                      '${job.offerCount} ${job.offerCount == 1 ? 'offer' : 'offers'}',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.cyanAccent,
                      ),
                    ),
                  )
                else
                  const Icon(
                    Icons.arrow_forward_ios,
                    color: AppTheme.textMuted,
                    size: 14,
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
