import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Fly Finder is a field guide for fly fishers: river greens, a mist-grey page, brass for
/// tackle, and a book serif for Latin binomials and titles. Controls and body copy stay on
/// the platform font so the app feels native.
abstract final class AppFonts {
  /// Source Serif 4 (bundled, SIL OFL 1.1). Used for titles and species names only.
  static const serif = 'SourceSerif4';
}

/// Semantic colours. Widgets read these through [FlyContext.fly] and never hard-code a hex
/// value, so every role has a light and a dark value (see `dark-mode.md`).
///
/// Contrast (WCAG, computed from the hex values below):
/// - light: ink 14.9:1, inkSecondary 7.4:1 on [canvas]; every level colour >= 6:1 on [card]
/// - dark: ink 15.6:1, inkSecondary 8.7:1 on [canvas]; every level colour >= 7.8:1 on [card]
@immutable
class FlyColors extends ThemeExtension<FlyColors> {
  const FlyColors({
    required this.brightness,
    required this.canvas,
    required this.card,
    required this.tint,
    required this.hairline,
    required this.ink,
    required this.inkSecondary,
    required this.river,
    required this.onRiver,
    required this.accent,
    required this.riverTint,
    required this.brass,
    required this.ripple,
    required this.levelHigh,
    required this.levelModerate,
    required this.levelLow,
    required this.levelNone,
    required this.warning,
    required this.onWarning,
    required this.warningBg,
  });

  final Brightness brightness;

  /// App background ("mist").
  final Color canvas;

  /// Cards and grouped lists.
  final Color card;

  /// Neutral chip and placeholder fill.
  final Color tint;
  final Color hairline;

  final Color ink;
  final Color inkSecondary;

  /// Fill of the primary action (buttons and the main home card).
  final Color river;
  final Color onRiver;

  /// River colour for text, icons and outlines drawn directly on [canvas] or [card].
  final Color accent;

  /// Soft green surface for selected and highlighted content.
  final Color riverTint;

  /// Brass means tackle: hook sizes, prices, shops. Readable as text on [canvas] and [card].
  final Color brass;

  /// Colour of the rise rings (the signature motif).
  final Color ripple;

  final Color levelHigh;
  final Color levelModerate;
  final Color levelLow;
  final Color levelNone;
  final Color warning;
  final Color onWarning;
  final Color warningBg;

  bool get isDark => brightness == Brightness.dark;

  /// Opacity of the tinted background behind coloured badges and tags.
  double get tintAlpha => isDark ? 0.16 : 0.12;

  Color level(String level) => switch (level) {
        'high_match' => levelHigh,
        'moderate_match' => levelModerate,
        'low_match' => levelLow,
        _ => levelNone,
      };

  static const light = FlyColors(
    brightness: Brightness.light,
    canvas: Color(0xFFF2F4EE),
    card: Color(0xFFFFFFFF),
    tint: Color(0xFFE6EBE2),
    hairline: Color(0xFFD5DACE),
    ink: Color(0xFF17211C),
    inkSecondary: Color(0xFF46524B),
    river: Color(0xFF1B4332),
    onRiver: Color(0xFFFFFFFF),
    accent: Color(0xFF1B4332),
    riverTint: Color(0xFFDCE9E1),
    brass: Color(0xFF7F5710),
    ripple: Color(0xFF2F6B55),
    levelHigh: Color(0xFF1F6B3A),
    levelModerate: Color(0xFF66650F),
    levelLow: Color(0xFF8F5509),
    levelNone: Color(0xFF56635D),
    warning: Color(0xFF744908),
    onWarning: Color(0xFFFFFFFF),
    warningBg: Color(0xFFFBF1DC),
  );

  static const dark = FlyColors(
    brightness: Brightness.dark,
    canvas: Color(0xFF0E1512),
    card: Color(0xFF17211D),
    tint: Color(0xFF22322B),
    hairline: Color(0xFF2B3A34),
    ink: Color(0xFFE8EDE6),
    inkSecondary: Color(0xFFA9B5AD),
    river: Color(0xFF2A6B55),
    onRiver: Color(0xFFFFFFFF),
    accent: Color(0xFF9AD8BC),
    riverTint: Color(0xFF1B3A2F),
    brass: Color(0xFFE0B45C),
    ripple: Color(0xFF9AD8BC),
    levelHigh: Color(0xFF7ED69A),
    levelModerate: Color(0xFFD3D26A),
    levelLow: Color(0xFFF0B05A),
    levelNone: Color(0xFFA9B5AD),
    warning: Color(0xFFF0C27A),
    onWarning: Color(0xFF2E2410),
    warningBg: Color(0xFF2E2410),
  );

  @override
  FlyColors copyWith() => this;

  @override
  FlyColors lerp(ThemeExtension<FlyColors>? other, double t) => other is FlyColors && t >= 0.5 ? other : this;
}

extension FlyContext on BuildContext {
  FlyColors get fly => Theme.of(this).extension<FlyColors>() ?? FlyColors.light;

  /// Body copy for reading paragraphs.
  TextStyle get readingStyle => (Theme.of(this).textTheme.bodyLarge ?? const TextStyle()).copyWith(color: fly.ink, height: 1.5);

  TextStyle get bodyStyle => (Theme.of(this).textTheme.bodyMedium ?? const TextStyle()).copyWith(color: fly.ink);

  /// Supporting lines under a title. 7:1 or better against the page in both appearances.
  TextStyle get secondaryStyle => (Theme.of(this).textTheme.bodyMedium ?? const TextStyle()).copyWith(color: fly.inkSecondary);

  /// Footnotes and credits. Never below 12 pt.
  TextStyle get captionStyle => (Theme.of(this).textTheme.bodySmall ?? const TextStyle()).copyWith(color: fly.inkSecondary);

  /// Serif display text (titles, pattern names).
  TextStyle serif(double size, {bool italic = false, Color? color, double height = 1.2}) => TextStyle(
        fontFamily: AppFonts.serif,
        fontWeight: FontWeight.w600,
        fontStyle: italic ? FontStyle.italic : FontStyle.normal,
        fontSize: size,
        height: height,
        color: color ?? fly.ink,
      );

  /// Latin binomials are always serif italic.
  TextStyle species(double size, {Color? color}) => serif(size, italic: true, color: color, height: 1.25);
}

abstract final class AppTheme {
  static ThemeData light() => _build(FlyColors.light);
  static ThemeData dark() => _build(FlyColors.dark);

  static ThemeData _build(FlyColors c) {
    final isDark = c.isDark;
    final brightness = c.brightness;
    final scheme = ColorScheme(
      brightness: brightness,
      primary: c.accent,
      onPrimary: isDark ? c.canvas : c.onRiver,
      primaryContainer: c.riverTint,
      onPrimaryContainer: c.ink,
      secondary: c.brass,
      onSecondary: isDark ? c.canvas : Colors.white,
      secondaryContainer: c.tint,
      onSecondaryContainer: c.ink,
      tertiary: c.brass,
      onTertiary: isDark ? c.canvas : Colors.white,
      error: isDark ? const Color(0xFFFFB4AB) : const Color(0xFFB3261E),
      onError: isDark ? const Color(0xFF410002) : Colors.white,
      surface: c.canvas,
      onSurface: c.ink,
      onSurfaceVariant: c.inkSecondary,
      outline: c.inkSecondary,
      outlineVariant: c.hairline,
      surfaceTint: Colors.transparent,
      surfaceContainerLowest: c.card,
      surfaceContainerLow: c.card,
      surfaceContainer: c.card,
      surfaceContainerHigh: c.tint,
      surfaceContainerHighest: c.tint,
      inverseSurface: c.ink,
      onInverseSurface: c.canvas,
      inversePrimary: c.river,
    );

    final base = ThemeData(useMaterial3: true, brightness: brightness, colorScheme: scheme, scaffoldBackgroundColor: c.canvas, extensions: [c]);
    final text = base.textTheme.apply(bodyColor: c.ink, displayColor: c.ink);

    // Type scale: body 17/15/13 pt (never below 12), serif for display only.
    final textTheme = text.copyWith(
      displaySmall: text.displaySmall?.copyWith(fontFamily: AppFonts.serif, fontWeight: FontWeight.w600, fontSize: 40, height: 1.05, letterSpacing: -0.6),
      headlineMedium: text.headlineMedium?.copyWith(fontFamily: AppFonts.serif, fontWeight: FontWeight.w600, fontSize: 30, height: 1.15, letterSpacing: -0.3),
      headlineSmall: text.headlineSmall?.copyWith(fontFamily: AppFonts.serif, fontWeight: FontWeight.w600, fontSize: 24, height: 1.2),
      titleLarge: text.titleLarge?.copyWith(fontFamily: AppFonts.serif, fontWeight: FontWeight.w600, fontSize: 22, height: 1.2),
      titleMedium: text.titleMedium?.copyWith(fontWeight: FontWeight.w600, fontSize: 17, height: 1.3),
      titleSmall: text.titleSmall?.copyWith(fontWeight: FontWeight.w600, fontSize: 15, height: 1.3),
      bodyLarge: text.bodyLarge?.copyWith(fontSize: 17, height: 1.4),
      bodyMedium: text.bodyMedium?.copyWith(fontSize: 15, height: 1.4),
      bodySmall: text.bodySmall?.copyWith(fontSize: 13, height: 1.35),
      labelLarge: text.labelLarge?.copyWith(fontWeight: FontWeight.w600, fontSize: 15),
      labelMedium: text.labelMedium?.copyWith(fontWeight: FontWeight.w600, fontSize: 13),
      labelSmall: text.labelSmall?.copyWith(fontWeight: FontWeight.w600, fontSize: 12),
    );

    const cardRadius = BorderRadius.all(Radius.circular(16));
    const controlRadius = BorderRadius.all(Radius.circular(14));
    final overlay = (isDark ? SystemUiOverlayStyle.light : SystemUiOverlayStyle.dark).copyWith(statusBarColor: Colors.transparent);

    return base.copyWith(
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        backgroundColor: c.canvas,
        foregroundColor: c.ink,
        elevation: 0,
        scrolledUnderElevation: 0.5,
        shadowColor: c.hairline,
        surfaceTintColor: Colors.transparent,
        centerTitle: false,
        systemOverlayStyle: overlay,
        titleTextStyle: TextStyle(fontFamily: AppFonts.serif, fontWeight: FontWeight.w600, fontSize: 20, color: c.ink),
      ),
      cardTheme: CardThemeData(
        color: c.card,
        elevation: 0,
        margin: EdgeInsets.zero,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: cardRadius, side: BorderSide(color: c.hairline)),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: c.river,
          foregroundColor: c.onRiver,
          minimumSize: const Size.fromHeight(56), // large touch targets for outdoor use
          elevation: 0,
          textStyle: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
          shape: const RoundedRectangleBorder(borderRadius: controlRadius),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(56),
          foregroundColor: c.accent,
          side: BorderSide(color: c.accent, width: 1.25),
          textStyle: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
          shape: const RoundedRectangleBorder(borderRadius: controlRadius),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: c.card,
        selectedColor: c.river,
        side: BorderSide(color: c.hairline),
        showCheckmark: false,
        labelStyle: TextStyle(color: c.ink, fontWeight: FontWeight.w600, fontSize: 15),
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: c.card,
        hintStyle: TextStyle(color: c.inkSecondary, fontSize: 17),
        prefixIconColor: c.inkSecondary,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(borderRadius: controlRadius, borderSide: BorderSide(color: c.hairline)),
        enabledBorder: OutlineInputBorder(borderRadius: controlRadius, borderSide: BorderSide(color: c.hairline)),
        focusedBorder: OutlineInputBorder(borderRadius: controlRadius, borderSide: BorderSide(color: c.accent, width: 2)),
      ),
      dividerTheme: DividerThemeData(color: c.hairline, space: 1, thickness: 1),
      progressIndicatorTheme: ProgressIndicatorThemeData(color: c.accent, linearTrackColor: c.tint),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: c.ink,
        contentTextStyle: TextStyle(color: c.canvas, fontSize: 15),
        shape: const RoundedRectangleBorder(borderRadius: controlRadius),
      ),
    );
  }
}
