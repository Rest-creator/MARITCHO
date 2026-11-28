import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// Reusable Maritcho Brand Logo lockup matching `frontend/src/components/ui/BrandLogo.tsx`.
/// Shows the official teardrop mark on a crisp white rounded tile with the wordmark.
class BrandLogo extends StatelessWidget {
  final double markSize;
  final double fontSize;
  final bool showWordmark;

  const BrandLogo({
    super.key,
    this.markSize = 28,
    this.fontSize = 20,
    this.showWordmark = true,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Container(
          width: markSize + 10,
          height: markSize + 10,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(10),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.15),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          padding: const EdgeInsets.all(4),
          child: Image.asset(
            'assets/brand/mark-96.png',
            width: markSize,
            height: markSize,
            fit: BoxFit.contain,
            errorBuilder: (_, _, _) => const Icon(
              Icons.water_drop,
              color: AppTheme.cyanAccent,
              size: 20,
            ),
          ),
        ),
        if (showWordmark) ...[
          const SizedBox(width: 10),
          Text(
            'Maritcho',
            style: TextStyle(
              fontSize: fontSize,
              fontWeight: FontWeight.w800,
              letterSpacing: -0.4,
              color: AppTheme.text,
            ),
          ),
        ],
      ],
    );
  }
}
