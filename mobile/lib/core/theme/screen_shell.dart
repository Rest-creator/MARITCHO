import 'package:flutter/material.dart';

import 'app_theme.dart';

/// Screen shell wrapper that applies the Maritcho royal indigo gradient background
/// and ambient glow spots, matching `frontend/src/components/ui/Screen.tsx`.
class ScreenShell extends StatelessWidget {
  final Widget child;
  final PreferredSizeWidget? appBar;
  final Widget? bottomNavigationBar;
  final Widget? floatingActionButton;
  final bool safeArea;

  const ScreenShell({
    super.key,
    required this.child,
    this.appBar,
    this.bottomNavigationBar,
    this.floatingActionButton,
    this.safeArea = true,
  });

  @override
  Widget build(BuildContext context) {
    Widget content = Stack(
      children: [
        // Ambient glows
        Positioned(
          left: -80,
          top: -60,
          child: Container(
            width: 280,
            height: 280,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppTheme.cyanAccent.withValues(alpha: 0.15),
            ),
          ),
        ),
        Positioned(
          right: -90,
          top: 300,
          child: Container(
            width: 260,
            height: 260,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppTheme.brandRoyal.withValues(alpha: 0.25),
            ),
          ),
        ),
        Positioned(
          left: -70,
          bottom: 100,
          child: Container(
            width: 240,
            height: 240,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppTheme.brandIndigoDeep.withValues(alpha: 0.35),
            ),
          ),
        ),
        // Child content
        Positioned.fill(child: safeArea ? SafeArea(child: child) : child),
      ],
    );

    return Container(
      decoration: const BoxDecoration(
        gradient: AppTheme.screenBackgroundGradient,
      ),
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: appBar,
        body: content,
        bottomNavigationBar: bottomNavigationBar,
        floatingActionButton: floatingActionButton,
      ),
    );
  }
}
