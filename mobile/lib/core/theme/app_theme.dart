import 'package:flutter/material.dart';

/// Palette: forest green, olive, sand, warm white and graphite.
abstract final class AppColors {
  static const forest = Color(0xFF1F3B2D);
  static const forestLight = Color(0xFF2E5641);
  static const olive = Color(0xFF6B7B3A);
  static const sand = Color(0xFFD9C8A3);
  static const sandLight = Color(0xFFF1E8D6);
  static const warmWhite = Color(0xFFFAF7F0);
  static const graphite = Color(0xFF2C2F33);
  static const muted = Color(0xFF6A6F66);
  static const border = Color(0xFFE3DCCB);

  // Match levels: readable outdoors, never relying on colour alone (labels are always shown).
  static const levelHigh = Color(0xFF2F6B3F);
  static const levelModerate = Color(0xFF7A7B22);
  static const levelLow = Color(0xFFA0661C);
  static const levelNone = Color(0xFF7D6F64);
  static const warning = Color(0xFF8A5A12);
  static const warningBg = Color(0xFFFBF1DC);
}

abstract final class AppTheme {
  static ThemeData light() {
    final scheme = ColorScheme.fromSeed(
      seedColor: AppColors.forest,
      primary: AppColors.forest,
      secondary: AppColors.olive,
      tertiary: AppColors.sand,
      surface: AppColors.warmWhite,
      onSurface: AppColors.graphite,
    );
    const radius = BorderRadius.all(Radius.circular(16));
    final base = ThemeData(useMaterial3: true, colorScheme: scheme, scaffoldBackgroundColor: AppColors.warmWhite);
    return base.copyWith(
      textTheme: base.textTheme.apply(bodyColor: AppColors.graphite, displayColor: AppColors.graphite).copyWith(
            headlineMedium: base.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w700, letterSpacing: -0.5),
            titleLarge: base.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
            titleMedium: base.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
          ),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.warmWhite,
        foregroundColor: AppColors.graphite,
        elevation: 0,
        scrolledUnderElevation: 1,
        centerTitle: false,
      ),
      cardTheme: const CardThemeData(
        color: Colors.white,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(borderRadius: radius, side: BorderSide(color: AppColors.border)),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(56), // large touch targets for outdoor use
          textStyle: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
          shape: const RoundedRectangleBorder(borderRadius: radius),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(56),
          foregroundColor: AppColors.forest,
          side: const BorderSide(color: AppColors.forest, width: 1.5),
          textStyle: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
          shape: const RoundedRectangleBorder(borderRadius: radius),
        ),
      ),
      chipTheme: base.chipTheme.copyWith(
        backgroundColor: AppColors.sandLight,
        side: BorderSide.none,
        labelStyle: const TextStyle(color: AppColors.graphite, fontWeight: FontWeight.w500),
      ),
      inputDecorationTheme: const InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(borderRadius: radius, borderSide: BorderSide(color: AppColors.border)),
        enabledBorder: OutlineInputBorder(borderRadius: radius, borderSide: BorderSide(color: AppColors.border)),
      ),
      dividerTheme: const DividerThemeData(color: AppColors.border, space: 1),
    );
  }
}
