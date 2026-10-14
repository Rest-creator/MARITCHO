import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';

/// Ports Main.dc.html's content/flow (headline, role picker, trust line,
/// "log in" link) using the app's own established AppTheme tokens rather
/// than the wireframe's literal dark/amber palette — AGENTS.md calls for
/// referencing the centralized design system, and this app's design
/// system today is AppTheme.lightTheme (Stormy-morning blue-gray).
class LandingPage extends StatelessWidget {
  const LandingPage({super.key});

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(24, 32, 24, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: AppTheme.primaryBlueGray,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(
                      Icons.handyman,
                      color: Colors.white,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 10),
                  const Text(
                    'Maricho',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              const SizedBox(height: 48),
              Text('Your skills are your CV.', style: textTheme.titleLarge),
              const SizedBox(height: 12),
              Text(
                'Find trusted hands for any job nearby, or get hired for '
                'the work you already know how to do.',
                style: textTheme.bodyMedium,
              ),
              const SizedBox(height: 32),
              Text(
                'How will you use Maricho?',
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: AppTheme.coolGray,
                  fontSize: 13,
                ),
              ),
              const SizedBox(height: 12),
              _RoleCard(
                icon: Icons.home_repair_service,
                title: 'I need work done',
                subtitle: 'Plumbing, repairs, gardening, a driver, house help and more',
                onTap: () =>
                    Navigator.of(context)
                        .pushNamed('/signup', arguments: 'BUYER'),
              ),
              const SizedBox(height: 12),
              _RoleCard(
                icon: Icons.construction,
                title: "I'm looking for work",
                subtitle:
                    'Get jobs for what you can do — no certificates needed',
                onTap: () =>
                    Navigator.of(context)
                        .pushNamed('/signup', arguments: 'WORKER'),
              ),
              const SizedBox(height: 32),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.lightBlueGray.withValues(alpha: 0.35),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.verified_user,
                      color: AppTheme.primaryBlueGray,
                      size: 18,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Every finished job leaves a review you can trust — for both sides.',
                        style: textTheme.bodyMedium?.copyWith(fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Center(
                child: TextButton(
                  onPressed: () =>
                      Navigator.of(context)
                          .pushNamed('/signup', arguments: 'BUYER'),
                  child: const Text('Already have an account? Log in'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RoleCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _RoleCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: AppTheme.lightBlueGray.withValues(alpha: 0.5),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(icon, color: AppTheme.darkBlueGray),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      style: Theme.of(context).textTheme.bodyMedium
                          ?.copyWith(fontSize: 13),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: AppTheme.coolGray),
            ],
          ),
        ),
      ),
    );
  }
}
