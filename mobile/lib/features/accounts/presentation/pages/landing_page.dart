import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/brand_logo.dart';
import '../../../../core/theme/screen_shell.dart';
import '../widgets/how_it_works_card.dart';

/// Redesigned Landing Page matching `frontend/src/features/accounts/WelcomeScreen.tsx` verbatim:
/// - Brand logo lockup: Maritcho
/// - Hero title: "Your skills are your CV."
/// - Hero subtitle: "Find trusted hands for any job nearby, or get hired for the work you already know how to do."
/// - Selection title: "How will you use Maritcho?"
/// - Buyer Card: "I need work done" / "Plumbing, repairs, solar, welding, building and more"
/// - Worker Card: "I'm looking for work" / "Get jobs for what you can do — no certificates needed"
/// - Interactive "How Maritcho works" carousel (4 of 4)
/// - Trust banner: "Every finished job leaves a review you can trust — for both sides."
/// - Link: "Don't have an account? Create account"
/// - Legal links: "Terms and Conditions · Privacy Policy"
class LandingPage extends StatelessWidget {
  const LandingPage({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenShell(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 8),
            // Header with Brand Logo
            const BrandLogo(),
            const SizedBox(height: 44),

            // Hero section
            Text(
              'Your skills are your CV.',
              style: Theme.of(context).textTheme.displayLarge?.copyWith(
                fontSize: 32,
                fontWeight: FontWeight.w800,
                letterSpacing: -0.6,
                color: AppTheme.text,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'Find trusted hands for any job nearby, or get hired for the work you already know how to do.',
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: AppTheme.textSecondary,
                height: 1.45,
                fontSize: 15,
              ),
            ),
            const SizedBox(height: 36),

            // Role selection prompt
            const Text(
              'How will you use Maritcho?',
              style: TextStyle(
                fontWeight: FontWeight.w700,
                color: AppTheme.text,
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 12),

            // Buyer Card
            _PathCard(
              icon: Icons.home_repair_service,
              iconColor: AppTheme.cyanAccent,
              iconBgColor: AppTheme.cyanTintSoft,
              title: 'I need work done',
              subtitle: 'Plumbing, repairs, solar, welding, building and more',
              onTap: () =>
                  Navigator.of(context)
                      .pushNamed('/signup', arguments: 'BUYER'),
            ),
            const SizedBox(height: 12),

            // Worker Card
            _PathCard(
              icon: Icons.work,
              iconColor: AppTheme.emeraldAccent,
              iconBgColor: AppTheme.emeraldTint,
              title: "I'm looking for work",
              subtitle: 'Get jobs for what you can do — no certificates needed',
              onTap: () =>
                  Navigator.of(context)
                      .pushNamed('/signup', arguments: 'WORKER'),
            ),
            const SizedBox(height: 28),

            // How Maritcho Works Interactive Card
            const HowItWorksCard(),
            const SizedBox(height: 28),

            // Trust Banner
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              decoration: BoxDecoration(
                color: AppTheme.glassSubtle,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.lineSubtle, width: 1.0),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.verified_outlined,
                    color: AppTheme.cyanAccent,
                    size: 20,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Every finished job leaves a review you can trust — for both sides.',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppTheme.textSecondary,
                        fontSize: 13,
                        height: 1.35,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Already have an account? Log in
            Center(
              child: GestureDetector(
                onTap: () => Navigator.of(context).pushNamed(
                  '/signup',
                  arguments: {'role': 'BUYER', 'isLogin': true},
                ),
                child: RichText(
                  text: const TextSpan(
                    style: TextStyle(
                      fontSize: 14,
                      color: AppTheme.textSecondary,
                    ),
                    children: [
                      TextSpan(text: "Already have an account? "),
                      TextSpan(
                        text: "Log in",
                        style: TextStyle(
                          color: AppTheme.cyanAccent,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Don't have an account? Create account
            Center(
              child: GestureDetector(
                onTap: () =>
                    Navigator.of(context)
                        .pushNamed('/signup', arguments: 'BUYER'),
                child: RichText(
                  text: const TextSpan(
                    style: TextStyle(
                      fontSize: 14,
                      color: AppTheme.textSecondary,
                    ),
                    children: [
                      TextSpan(text: "Don't have an account? "),
                      TextSpan(
                        text: "Create account",
                        style: TextStyle(
                          color: AppTheme.cyanAccent,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Terms and Conditions · Privacy Policy
            Center(
              child: Text(
                'Terms and Conditions  ·  Privacy Policy',
                style: TextStyle(
                  fontSize: 12,
                  color: AppTheme.textMuted.withValues(alpha: 0.8),
                  decoration: TextDecoration.underline,
                ),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}

class _PathCard extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final Color iconBgColor;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _PathCard({
    required this.icon,
    required this.iconColor,
    required this.iconBgColor,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppTheme.glassStrong,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.line, width: 1.0),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(18),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: iconBgColor,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: iconColor.withValues(alpha: 0.35),
                      width: 1.0,
                    ),
                  ),
                  child: Icon(icon, color: iconColor, size: 24),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.text,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        subtitle,
                        style: const TextStyle(
                          fontSize: 13,
                          color: AppTheme.textSecondary,
                          height: 1.35,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                const Icon(
                  Icons.arrow_forward_ios,
                  color: AppTheme.textMuted,
                  size: 16,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
