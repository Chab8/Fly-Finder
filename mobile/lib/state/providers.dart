import 'dart:math';
import 'dart:ui' show PlatformDispatcher;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/config/app_config.dart';
import '../models/catalog.dart';
import '../models/commerce.dart';
import '../models/identification.dart';
import '../services/fly_finder_api.dart';
import '../services/image_source_service.dart';

/// Overridden in main() once SharedPreferences is ready.
final sharedPreferencesProvider = Provider<SharedPreferences>((ref) => throw UnimplementedError('override in main()'));

final appConfigProvider = Provider<AppConfig>((ref) => AppConfig.fromEnvironment());

/// Random, anonymous id for this install. Lets the backend show this device its own history.
final clientIdProvider = Provider<String>((ref) {
  final prefs = ref.watch(sharedPreferencesProvider);
  const key = 'client_id';
  final existing = prefs.getString(key);
  if (existing != null) return existing;
  final random = Random.secure();
  final hex = List.generate(16, (_) => random.nextInt(256).toRadixString(16).padLeft(2, '0')).join();
  final id = '${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
  prefs.setString(key, id);
  return id;
});

String deviceLanguage() => PlatformDispatcher.instance.locale.languageCode == 'es' ? 'es' : 'en';

String? deviceCountry() => PlatformDispatcher.instance.locale.countryCode;

final apiProvider = Provider<FlyFinderApi>((ref) {
  return DioFlyFinderApi(baseUrl: ref.watch(appConfigProvider).apiBaseUrl, clientId: ref.watch(clientIdProvider), language: deviceLanguage);
});

final imageSourceProvider = Provider<ImageSourceService>((ref) => PickerImageSourceService());

// ------------------------------------------------------------ catalog queries
typedef CatalogQuery = ({String query, String? filter});

final organismListProvider = FutureProvider.autoDispose.family<CatalogPage<OrganismSummary>, CatalogQuery>(
  (ref, q) => ref.watch(apiProvider).organisms(query: q.query, group: q.filter),
);

final flyListProvider = FutureProvider.autoDispose.family<CatalogPage<FlyPatternSummary>, CatalogQuery>(
  (ref, q) => ref.watch(apiProvider).flies(query: q.query, category: q.filter),
);

final organismDetailProvider = FutureProvider.autoDispose.family<OrganismDetail, String>((ref, id) => ref.watch(apiProvider).organism(id));

final flyDetailProvider = FutureProvider.autoDispose.family<FlyPatternDetail, String>((ref, id) => ref.watch(apiProvider).fly(id));

final flyProductsProvider = FutureProvider.autoDispose.family<List<ProductInfo>, String>(
  (ref, id) => ref.watch(apiProvider).flyProducts(id, country: deviceCountry()),
);

final historyProvider = FutureProvider.autoDispose<List<IdentificationSummary>>((ref) => ref.watch(apiProvider).history());

final storedIdentificationProvider = FutureProvider.autoDispose.family<IdentificationResult, String>(
  (ref, id) => ref.watch(apiProvider).storedIdentification(id),
);
