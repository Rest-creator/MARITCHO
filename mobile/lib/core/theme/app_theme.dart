import 'package:flutter/material.dart';

class AppTheme {
  // Combination 1: Stormy morning (Blue-gray)
  // Trustworthy and reliable, excellent for a service marketplace.
  static const Color primaryBlueGray = Color(0xFF607D8B);
  static const Color darkBlueGray = Color(0xFF455A64);
  static const Color lightBlueGray = Color(0xFFCFD8DC);
  
  // Clean backgrounds (Ink wash inspiration)
  static const Color softIvory = Color(0xFFFAFAFA);
  static const Color coolGray = Color(0xFF9E9E9E);
  static const Color charcoalBlack = Color(0xFF212121);

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: softIvory,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryBlueGray,
        primary: primaryBlueGray,
        onPrimary: Colors.white,
        secondary: darkBlueGray,
        background: softIvory,
        surface: Colors.white,
        onSurface: charcoalBlack,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        scrolledUnderElevation: 0,
        iconTheme: IconThemeData(color: charcoalBlack),
        titleTextStyle: TextStyle(
          color: charcoalBlack,
          fontSize: 17,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.41, // Apple Design optical tracking
        ),
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(color: charcoalBlack, fontSize: 34, fontWeight: FontWeight.bold, letterSpacing: 0.37),
        titleLarge: TextStyle(color: charcoalBlack, fontSize: 28, fontWeight: FontWeight.bold, letterSpacing: 0.36),
        bodyLarge: TextStyle(color: charcoalBlack, fontSize: 17, fontWeight: FontWeight.w400, letterSpacing: -0.41),
        bodyMedium: TextStyle(color: charcoalBlack, fontSize: 15, fontWeight: FontWeight.w400, letterSpacing: -0.24),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryBlueGray,
          foregroundColor: Colors.white,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12), // Apple Design smooth corners
          ),
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
          textStyle: const TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w600,
            letterSpacing: -0.41,
          ),
        ),
      ),
      cardTheme: CardTheme(
        color: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: lightBlueGray, width: 0.5),
        ),
      ),
    );
  }
}
