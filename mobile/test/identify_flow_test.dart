import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fly_finder/core/network/api_failure.dart';
import 'package:fly_finder/models/identification.dart';
import 'package:fly_finder/services/image_source_service.dart';

import 'helpers.dart';

void main() {
  testWidgets('home shows both identification functions and navigates', (tester) async {
    await pumpApp(tester, api: FakeApi());
    expect(find.text('Identify an organism'), findsOneWidget);
    expect(find.text('Identify a fly'), findsOneWidget);
    expect(find.text('Catalog'), findsOneWidget);
    await tester.tap(find.byKey(const Key('home-identify-fly')));
    await tester.pumpAndSettle();
    expect(find.text('No photo selected yet'), findsOneWidget);
    expect(find.byKey(const Key('capture-analyze')), findsNothing);
  });

  testWidgets('home is localized in Spanish', (tester) async {
    await pumpApp(tester, api: FakeApi(), locale: const Locale('es'));
    expect(find.text('Identificar organismo'), findsOneWidget);
    expect(find.text('Identificar mosca'), findsOneWidget);
  });

  testWidgets('selecting a photo shows a preview and the analyze button', (tester) async {
    final images = FakeImageSource(photo: PickedPhoto(bytes: tinyPng, filename: 'bug.png'));
    await pumpApp(tester, api: FakeApi(), images: images, initialLocation: '/identify/organism');
    await tester.tap(find.byKey(const Key('capture-gallery')));
    await tester.pumpAndSettle();
    expect(images.requests, [PhotoSource.gallery]);
    expect(find.byKey(const Key('capture-preview')), findsOneWidget);
    expect(find.byKey(const Key('capture-analyze')), findsOneWidget);
    expect(find.text('Change photo'), findsOneWidget);
  });

  testWidgets('unsupported file types are rejected before upload', (tester) async {
    final images = FakeImageSource(photo: PickedPhoto(bytes: tinyPng, filename: 'clip.gif'));
    await pumpApp(tester, api: FakeApi(), images: images, initialLocation: '/identify/fly');
    await tester.tap(find.byKey(const Key('capture-gallery')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Unsupported file type'), findsOneWidget);
    expect(find.byKey(const Key('capture-analyze')), findsNothing);
  });

  testWidgets('permission denial is explained', (tester) async {
    await pumpApp(tester, api: FakeApi(), images: FakeImageSource(denied: true), initialLocation: '/identify/organism');
    await tester.tap(find.byKey(const Key('capture-camera')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Permission to use the camera'), findsOneWidget);
  });

  testWidgets('full organism flow: loading phases then result with recommendations', (tester) async {
    final api = FakeApi(identifyResult: OrganismIdentification.fromJson(fixtureMap('organism_result.json')))..holdIdentify = Completer();
    final images = FakeImageSource(photo: PickedPhoto(bytes: tinyPng, filename: 'bug.png'));
    await pumpApp(tester, api: api, images: images, initialLocation: '/identify/organism');
    await tester.tap(find.byKey(const Key('capture-gallery')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('capture-analyze')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));
    expect(find.text('Analyzing on the server'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsWidgets);

    api.holdIdentify!.complete();
    await tester.pumpAndSettle();
    expect(api.calls, ['identify:organism']);
    expect(find.text('Organism result'), findsOneWidget);
    expect(find.text('High match'), findsOneWidget);
    expect(find.text('Baetis'), findsWidgets);
    await tester.scrollUntilVisible(find.text('Recommended flies'), 300);
    expect(find.text('Recommended flies'), findsOneWidget);
    expect(find.text('Documented for this life stage'), findsWidgets);
  });

  testWidgets('API unavailable shows an error with retry', (tester) async {
    final api = FakeApi(identifyError: const ApiFailure(FailureKind.unavailable, code: 'analysis_unavailable'));
    final images = FakeImageSource(photo: PickedPhoto(bytes: tinyPng, filename: 'bug.png'));
    await pumpApp(tester, api: api, images: images, initialLocation: '/identify/organism');
    await tester.tap(find.byKey(const Key('capture-gallery')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('capture-analyze')));
    await tester.pumpAndSettle();
    expect(find.textContaining('temporarily unavailable'), findsOneWidget);
    expect(find.text('Retry'), findsOneWidget);

    api
      ..identifyError = null
      ..identifyResult = OrganismIdentification.fromJson(fixtureMap('organism_result.json'));
    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();
    expect(find.text('Organism result'), findsOneWidget);
  });

  testWidgets('network failure message', (tester) async {
    final api = FakeApi(identifyError: const ApiFailure(FailureKind.network));
    final images = FakeImageSource(photo: PickedPhoto(bytes: tinyPng, filename: 'fly.jpg'));
    await pumpApp(tester, api: api, images: images, initialLocation: '/identify/fly');
    await tester.tap(find.byKey(const Key('capture-gallery')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('capture-analyze')));
    await tester.pumpAndSettle();
    expect(find.textContaining('No connection to the server'), findsOneWidget);
  });
}
