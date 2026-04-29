import "package:flutter/material.dart";
import "package:google_fonts/google_fonts.dart";

/// Aligns with Django minimal theme (soft gradient, Quicksand, accent blues/greens).
class MinimalColors {
  MinimalColors._();

  static const Color primaryBlue = Color(0xFF2196F3);
  static const Color primaryGreen = Color(0xFF4CAF50);
  static const Color primaryYellow = Color(0xFFFFD600);
  static const Color neutralGray = Color(0xFFE0E0E0);
  static const Color gradientStart = Color(0xFFF3F6FA);
  static const Color gradientEnd = Color(0xFFE9EAFC);
  static const Color surfaceGlass = Color(0xE6FFFFFF);
  static const Color textPrimary = Color(0xFF1A1A2E);
  static const Color textSecondary = Color(0xFF5C5C6E);
}

ThemeData buildMinimalTheme() {
  final base = ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    colorScheme: ColorScheme.fromSeed(
      seedColor: MinimalColors.primaryBlue,
      primary: MinimalColors.primaryBlue,
      secondary: MinimalColors.primaryGreen,
      tertiary: MinimalColors.primaryYellow,
      surface: MinimalColors.surfaceGlass,
    ),
    scaffoldBackgroundColor: MinimalColors.gradientStart,
  );

  return base.copyWith(
    textTheme: GoogleFonts.quicksandTextTheme(base.textTheme).apply(
      bodyColor: MinimalColors.textPrimary,
      displayColor: MinimalColors.textPrimary,
    ),
    appBarTheme: AppBarTheme(
      centerTitle: true,
      elevation: 0,
      scrolledUnderElevation: 0,
      backgroundColor: Colors.transparent,
      foregroundColor: MinimalColors.textPrimary,
      titleTextStyle: GoogleFonts.orbitron(
        fontSize: 22,
        fontWeight: FontWeight.w600,
        color: MinimalColors.primaryBlue,
      ),
    ),
    cardTheme: CardTheme(
      elevation: 0,
      color: MinimalColors.surfaceGlass,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white.withOpacity(0.85),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
  );
}

/// Full-viewport soft gradient used behind scaffolds.
class MinimalPageBackground extends StatelessWidget {
  const MinimalPageBackground({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            MinimalColors.gradientStart,
            MinimalColors.gradientEnd,
          ],
        ),
      ),
      child: child,
    );
  }
}
