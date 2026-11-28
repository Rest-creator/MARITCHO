import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';

class Chapter {
  final String title;
  final String caption;
  final IconData icon;

  const Chapter({
    required this.title,
    required this.caption,
    required this.icon,
  });
}

const List<Chapter> howItWorksChapters = [
  Chapter(
    title: "Post the job",
    caption: "Say what's wrong. A photo or a voice note is enough.",
    icon: Icons.post_add_rounded,
  ),
  Chapter(
    title: "Get prices",
    caption: "Workers nearby send their price. You choose who to hire.",
    icon: Icons.payments_outlined,
  ),
  Chapter(
    title: "The work gets done",
    caption: "Your worker comes to you. Follow the job as it happens.",
    icon: Icons.engineering_rounded,
  ),
  Chapter(
    title: "Sign off",
    caption: "Confirm and pay. Every job builds the worker's record.",
    icon: Icons.verified_rounded,
  ),
];

/// Interactive "How Maritcho works" card matching `frontend/src/features/onboarding/HowItWorks.tsx`:
/// - Stage header: "How Maritcho works" + "X of 4"
/// - Visual illustrative stage with active stage graphic
/// - Chapter title and caption
/// - Back and Next stepper buttons + pagination dots
class HowItWorksCard extends StatefulWidget {
  const HowItWorksCard({super.key});

  @override
  State<HowItWorksCard> createState() => _HowItWorksCardState();
}

class _HowItWorksCardState extends State<HowItWorksCard> {
  int _currentChapter = 0;

  void _next() {
    if (_currentChapter < howItWorksChapters.length - 1) {
      setState(() => _currentChapter++);
    }
  }

  void _back() {
    if (_currentChapter > 0) {
      setState(() => _currentChapter--);
    }
  }

  @override
  Widget build(BuildContext context) {
    final chapter = howItWorksChapters[_currentChapter];
    final isFirst = _currentChapter == 0;
    final isLast = _currentChapter == howItWorksChapters.length - 1;

    return Container(
      decoration: BoxDecoration(
        color: AppTheme.glassStrong,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.line, width: 1.0),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header: Title and Step Counter
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'How Maritcho works',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.text,
                ),
              ),
              Text(
                '${_currentChapter + 1} of ${howItWorksChapters.length}',
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textMuted,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Illustrative Stage
          Container(
            height: 110,
            decoration: BoxDecoration(
              color: AppTheme.glassFaint,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.lineFaint),
            ),
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Ambient glow
                Container(
                  width: 70,
                  height: 70,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppTheme.cyanAccent.withValues(alpha: 0.15),
                  ),
                ),
                // Icon Illustration for this chapter
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        color: AppTheme.cyanTintSoft,
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: AppTheme.cyanAccent.withValues(alpha: 0.4),
                        ),
                      ),
                      child: Icon(
                        chapter.icon,
                        color: AppTheme.cyanAccent,
                        size: 26,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Caption Title & Text
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 200),
            child: Column(
              key: ValueKey(_currentChapter),
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  chapter.title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.text,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  chapter.caption,
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppTheme.textSecondary,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Controls: Back, Dots, Next
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Back Button
              TextButton(
                onPressed: isFirst ? null : _back,
                style: TextButton.styleFrom(
                  foregroundColor: AppTheme.textSecondary,
                  disabledForegroundColor: AppTheme.textMuted.withValues(
                    alpha: 0.3,
                  ),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 8,
                  ),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.arrow_back, size: 16),
                    SizedBox(width: 4),
                    Text(
                      'Back',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),

              // Dots
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  for (int i = 0; i < howItWorksChapters.length; i++)
                    GestureDetector(
                      onTap: () => setState(() => _currentChapter = i),
                      child: Container(
                        margin: const EdgeInsets.symmetric(horizontal: 4),
                        width: _currentChapter == i ? 18 : 6,
                        height: 6,
                        decoration: BoxDecoration(
                          color: _currentChapter == i
                              ? AppTheme.cyanAccent
                              : AppTheme.lineBold,
                          borderRadius: BorderRadius.circular(3),
                        ),
                      ),
                    ),
                ],
              ),

              // Next Button
              TextButton(
                onPressed: isLast ? null : _next,
                style: TextButton.styleFrom(
                  foregroundColor: AppTheme.cyanAccent,
                  disabledForegroundColor: AppTheme.textMuted.withValues(
                    alpha: 0.3,
                  ),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 8,
                  ),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'Next',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    SizedBox(width: 4),
                    Icon(Icons.arrow_forward, size: 16),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
