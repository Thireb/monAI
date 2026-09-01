import "package:flutter/material.dart";
import "package:google_fonts/google_fonts.dart";

/// Action-first mobile palette (monAI accents, quieter than web glass stacks).
class MinimalColors {
  MinimalColors._();

  static const Color primaryBlue = Color(0xFF2196F3);
  static const Color primaryGreen = Color(0xFF4CAF50);
  static const Color primaryYellow = Color(0xFFFFD600);
  static const Color neutralGray = Color(0xFFE0E0E0);
  static const Color gradientStart = Color(0xFFF3F6FA);
  static const Color gradientEnd = Color(0xFFE9EAFC);
  static const Color surfaceQuiet = Color(0xFFF7F8FC);
  static const Color textPrimary = Color(0xFF1A1A2E);
  static const Color textSecondary = Color(0xFF5C5C6E);
  static const Color inputFieldFill = Color(0xD9FFFFFF);

  /// Legacy alias used by older screens.
  static const Color surfaceGlass = surfaceQuiet;
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
      surface: MinimalColors.surfaceQuiet,
    ),
    scaffoldBackgroundColor: Colors.transparent,
  );

  final text = GoogleFonts.quicksandTextTheme(base.textTheme).apply(
    bodyColor: MinimalColors.textPrimary,
    displayColor: MinimalColors.textPrimary,
  );

  return base.copyWith(
    textTheme: text,
    appBarTheme: AppBarTheme(
      centerTitle: false,
      elevation: 0,
      scrolledUnderElevation: 0,
      backgroundColor: Colors.transparent,
      foregroundColor: MinimalColors.textPrimary,
      titleTextStyle: text.titleLarge?.copyWith(fontWeight: FontWeight.w700),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: MinimalColors.surfaceQuiet,
      indicatorColor: MinimalColors.primaryBlue.withValues(alpha: 0.15),
      labelTextStyle: WidgetStatePropertyAll(
        text.labelMedium?.copyWith(fontWeight: FontWeight.w600),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: MinimalColors.inputFieldFill,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
    listTileTheme: const ListTileThemeData(
      contentPadding: EdgeInsets.symmetric(horizontal: 4, vertical: 2),
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

/// Prefer [ListTile] / ink rows; keep this only when a bordered group is needed.
Widget minimalCard({required Widget child}) {
  return Material(
    color: Colors.white.withValues(alpha: 0.72),
    borderRadius: BorderRadius.circular(14),
    child: child,
  );
}
