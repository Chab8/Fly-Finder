import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app/app.dart';
import 'state/providers.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
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
