import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app/app.dart';
import 'state/providers.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Bundled font licence, shown in the app's licence page.
  LicenseRegistry.addLicense(() async* {
    yield LicenseEntryWithLineBreaks(['Source Serif 4'], await rootBundle.loadString('assets/fonts/SourceSerif4-LICENSE.md'));
  });
  final prefs = await SharedPreferences.getInstance();
  runApp(
    ProviderScope(
      // Failed requests show an error with a Retry button instead of retrying silently.
      retry: (retryCount, error) => null,
      overrides: [sharedPreferencesProvider.overrideWithValue(prefs)],
      child: const FlyFinderApp(),
    ),
  );
}
