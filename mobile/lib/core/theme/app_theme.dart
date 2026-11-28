import 'package:flutter/material.dart';

/// Maritcho design tokens — sampled directly from the official Maritcho
/// teardrop banners & 2026 Logo Presentation (mirrors `frontend/src/styles/tokens.css`):
/// - Teardrop 1: Crisp White (#ffffff)
/// - Teardrop 2: Royal Indigo Blue (#222576 -> #2d2e83 -> #34519f)
/// - Teardrop 3: Vibrant Sky Cyan (#00abe3 -> #00ace8)
class AppTheme {
  // Brand Teardrop Colors
  static const Color brandIndigoDeep = Color(0xFF222576);
  static const Color brandNavy = Color(0xFF2D2E83);
  static const Color brandRoyal = Color(0xFF34519F);
  static const Color brandBlue = Color(0xFF00ABE3);
  static const Color brandCyan = Color(0xFF00ABE3);

  // Surfaces & Backgrounds
  static const Color colorBg = Color(0xFF26287D);
  static const Color colorBgRaised = Color(0xFF2D2E83);
  static const Color colorSheet = Color(0xFF242678);
  static const Color colorScrim = Color(0xC2121444); // rgba(18, 20, 68, 0.76)
  static const Color colorBar = Color(0xE0222576); // rgba(34, 37, 118, 0.88)
  static const Color colorNav = Color(0xE0222576);

  // Glass & Borders
  static const Color glassFaint = Color(0x0DFFFFFF); // 5%
  static const Color glassSubtle = Color(0x12FFFFFF); // 7%
  static const Color glass = Color(0x17FFFFFF); // 9%
  static const Color glassStrong = Color(0x1CFFFFFF); // 11%
  static const Color glassBold = Color(0x24FFFFFF); // 14%
  static const Color glassSelected = Color(
    0x3D00ABE3,
  ); // rgba(0, 171, 227, 0.24)

  static const Color lineFaint = Color(0x1AFFFFFF); // 10%
  static const Color lineSubtle = Color(0x24FFFFFF); // 14%
  static const Color line = Color(0x2EFFFFFF); // 18%
  static const Color lineStrong = Color(0x38FFFFFF); // 22%
  static const Color lineBold = Color(0x47FFFFFF); // 28%

  // Text Hierarchy
  static const Color text = Color(0xFFFFFFFF);
  static const Color textSoft = Color(0xFFF0F9FF);
  static const Color textSecondary = Color(0xFFDBEAFE);
  static const Color textMuted = Color(0xFF93C5FD);
  static const Color textDim = Color(0xFF60A5FA);

  // Primary Accent (Vibrant Sky Cyan #00ABE3)
  static const Color cyanAccent = Color(0xFF00ABE3);
  static const Color cyanLight = Color(0xFF29C0F2);
  static const Color cyanLighter = Color(0xFF67D6FA);
  static const Color cyanPale = Color(0xFFE0F7FF);
  static const Color cyanTint = Color(0x3800ABE3); // 22%
  static const Color cyanTintSoft = Color(0x2400ABE3); // 14%
  static const Color cyanEdge = Color(0x8500ABE3); // 52%

  // Secondary / Worker Emerald Accent
  static const Color emeraldAccent = Color(0xFF00ACE8);
  static const Color emeraldLight = Color(0xFF38C6F4);
  static const Color emeraldTint = Color(0x3300ACE8);
  static const Color emeraldEdge = Color(0x7A00ACE8);

  // Status Colors
  static const Color danger = Color(0xFFF87171);
  static const Color dangerTint = Color(0x24F87171);
  static const Color dangerEdge = Color(0x66F87171);

  // Legacy mappings for backwards-compatibility
  static const Color primaryBlueGray = cyanAccent;
  static const Color darkBlueGray = brandNavy;
  static const Color lightBlueGray = lineSubtle;
  static const Color softIvory = colorBg;
  static const Color coolGray = textMuted;
  static const Color charcoalBlack = text;

  // Background Gradient
  static const LinearGradient brandGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [brandIndigoDeep, brandNavy, brandRoyal],
    stops: [0.0, 0.48, 1.0],
  );

  static const LinearGradient screenBackgroundGradient = LinearGradient(
    begin: Alignment(-0.8, -1.0),
    end: Alignment(0.8, 1.0),
    colors: [Color(0xFF222576), Color(0xFF2D2E83), Color(0xFF34519F)],
    stops: [0.0, 0.52, 1.0],
  );

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: colorBg,
      colorScheme: const ColorScheme.dark(
        primary: cyanAccent,
        onPrimary: Colors.white,
        secondary: brandRoyal,
        onSecondary: Colors.white,
        surface: colorSheet,
        onSurface: text,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        scrolledUnderElevation: 0,
        iconTheme: IconThemeData(color: text),
        titleTextStyle: TextStyle(
          color: text,
          fontSize: 18,
          fontWeight: FontWeight.w700,
          letterSpacing: -0.2,
        ),
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(
          color: text,
          fontSize: 34,
          fontWeight: FontWeight.bold,
          letterSpacing: -0.5,
        ),
        titleLarge: TextStyle(
          color: text,
          fontSize: 26,
          fontWeight: FontWeight.bold,
          letterSpacing: -0.3,
        ),
        titleMedium: TextStyle(
          color: text,
          fontSize: 18,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.2,
        ),
        bodyLarge: TextStyle(
          color: textSoft,
          fontSize: 16,
          fontWeight: FontWeight.w400,
          letterSpacing: -0.1,
        ),
        bodyMedium: TextStyle(
          color: textSecondary,
          fontSize: 14,
          fontWeight: FontWeight.w400,
        ),
        bodySmall: TextStyle(
          color: textMuted,
          fontSize: 12,
          fontWeight: FontWeight.w400,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: cyanAccent,
          foregroundColor: Colors.white,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w700,
            letterSpacing: -0.2,
          ),
        ),
      ),
      cardTheme: CardThemeData(
        color: glass,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: lineSubtle, width: 1.0),
        ),
      ),
    );
  }

  // Set default theme to the official dark/royal indigo palette
  static ThemeData get lightTheme => darkTheme;
}
