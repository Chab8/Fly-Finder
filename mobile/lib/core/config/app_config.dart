import 'dart:io' show Platform;

/// Build-time configuration, set with --dart-define. No secrets live here:
/// every API key stays on the backend.
class AppConfig {
  const AppConfig({required this.apiBaseUrl, required this.appName, required this.maxUploadMb});

  /// Working product name; not a final brand. Override with --dart-define=APP_NAME=...
  static const String _appName = String.fromEnvironment('APP_NAME', defaultValue: 'Fly Finder');
  static const String _apiBaseUrl = String.fromEnvironment('API_BASE_URL');

  final String apiBaseUrl;
  final String appName;
  final int maxUploadMb;

  factory AppConfig.fromEnvironment() {
    return AppConfig(apiBaseUrl: _apiBaseUrl.isNotEmpty ? _apiBaseUrl : _localDefault(), appName: _appName, maxUploadMb: 12);
  }

  /// The Android emulator reaches the host machine at 10.0.2.2; the iOS simulator at localhost.
  static String _localDefault() {
    try {
      if (Platform.isAndroid) return 'http://10.0.2.2:8000';
    } catch (_) {
      // Platform is unavailable on web/tests.
    }
    return 'http://localhost:8000';
  }
}
