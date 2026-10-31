import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fly_finder/app/app.dart';
import 'package:fly_finder/app/router.dart';
import 'package:fly_finder/core/network/api_failure.dart';
import 'package:fly_finder/models/catalog.dart';
import 'package:fly_finder/models/commerce.dart';
import 'package:fly_finder/models/identification.dart';
import 'package:fly_finder/models/json.dart';
import 'package:fly_finder/services/fly_finder_api.dart';
import 'package:fly_finder/services/image_source_service.dart';
import 'package:fly_finder/state/providers.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// JSON generated from the real backend (see backend/tests/test_contract_fixtures.py).
dynamic fixture(String name) => jsonDecode(File('test/fixtures/$name').readAsStringSync());
Json fixtureMap(String name) => Json.from(fixture(name) as Map);

// A valid 1x1 PNG.
final Uint8List tinyPng = base64Decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==');

class FakeImageSource implements ImageSourceService {
  FakeImageSource({this.photo, this.denied = false});
  PickedPhoto? photo;
  bool denied;
  final List<PhotoSource> requests = [];

  @override
  Future<PickedPhoto?> pick(PhotoSource source) async {
    requests.add(source);
    if (denied) throw PhotoPermissionDenied();
    return photo;
  }
}

class FakeApi implements FlyFinderApi {
  FakeApi({
    this.identifyResult,
    this.identifyError,
    this.organismPage,
    this.flyPage,
    this.products = const [],
    this.historyItems = const [],
  });

  IdentificationResult? identifyResult;
  ApiFailure? identifyError;
  Completer<void>? holdIdentify;
  CatalogPage<OrganismSummary>? organismPage;
  CatalogPage<FlyPatternSummary>? flyPage;
  List<ProductInfo> products;
  List<IdentificationSummary> historyItems;
  final List<String> calls = [];

  @override
  Future<IdentificationResult> identify(IdentifyMode mode, List<int> imageBytes, String filename, {UploadProgress? onProgress, String? country}) async {
    calls.add('identify:${mode.name}');
    onProgress?.call(0.5);
    onProgress?.call(1);
    if (holdIdentify != null) await holdIdentify!.future;
    if (identifyError != null) throw identifyError!;
    return identifyResult!;
  }

  @override
  Future<CatalogPage<OrganismSummary>> organisms({String? query, String? group, int limit = 100}) async {
    calls.add('organisms:${query ?? ''}:${group ?? ''}');
    return organismPage ?? const CatalogPage([], 0);
  }

  @override
  Future<CatalogPage<FlyPatternSummary>> flies({String? query, String? category, int limit = 100}) async {
    calls.add('flies:${query ?? ''}:${category ?? ''}');
    return flyPage ?? const CatalogPage([], 0);
  }

  @override
  Future<OrganismDetail> organism(String id) async => OrganismDetail.fromJson(fixtureMap('organism_detail.json'));

  @override
  Future<FlyPatternDetail> fly(String id) async => FlyPatternDetail.fromJson(fixtureMap('fly_detail.json'));

  @override
  Future<List<ProductInfo>> flyProducts(String flyId, {String? country}) async => products;

  @override
  Future<List<IdentificationSummary>> history() async => historyItems;

  @override
  Future<IdentificationResult> storedIdentification(String id) async => identifyResult!;
}

Future<void> pumpApp(
  WidgetTester tester, {
  required FakeApi api,
  FakeImageSource? images,
  String initialLocation = '/',
  Locale locale = const Locale('en'),
}) async {
  SharedPreferences.setMockInitialValues({});
  final prefs = await SharedPreferences.getInstance();
  // A tall phone-sized surface so long result screens can be scrolled in tests.
  tester.view.physicalSize = const Size(1170, 2532);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    ProviderScope(
      retry: (retryCount, error) => null,
      overrides: [
        sharedPreferencesProvider.overrideWithValue(prefs),
        apiProvider.overrideWithValue(api),
        imageSourceProvider.overrideWithValue(images ?? FakeImageSource()),
      ],
      child: FlyFinderApp(router: buildRouter(initialLocation: initialLocation), locale: locale),
    ),
  );
  await tester.pumpAndSettle();
}
