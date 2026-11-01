import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/theme/app_theme.dart';
import '../l10n/app_localizations.dart';
import '../state/providers.dart';
import 'router.dart';

class FlyFinderApp extends ConsumerStatefulWidget {
  const FlyFinderApp({super.key, this.router, this.locale});

  /// Injected in tests; built once otherwise.
  final GoRouter? router;
  final Locale? locale;

  @override
  ConsumerState<FlyFinderApp> createState() => _FlyFinderAppState();
}

class _FlyFinderAppState extends ConsumerState<FlyFinderApp> {
  late final GoRouter _router = widget.router ?? buildRouter();

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: ref.watch(appConfigProvider).appName,
      theme: AppTheme.light(),
      // Follows the system appearance; there is deliberately no in-app switch.
      darkTheme: AppTheme.dark(),
      themeMode: ThemeMode.system,
      routerConfig: _router,
      locale: widget.locale,
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      debugShowCheckedModeBanner: false,
    );
  }
}
