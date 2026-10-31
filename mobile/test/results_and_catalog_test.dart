import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fly_finder/features/catalog/product_tile.dart';
import 'package:fly_finder/models/catalog.dart';
import 'package:fly_finder/models/commerce.dart';
import 'package:fly_finder/models/identification.dart';
import 'package:fly_finder/models/json.dart';

import 'helpers.dart';

void main() {
  testWidgets('not-compatible result shows the reason and no recommendations', (tester) async {
    final api = FakeApi(identifyResult: OrganismIdentification.fromJson(fixtureMap('organism_not_compatible.json')));
    await pumpApp(tester, api: api, initialLocation: '/history/abc');
    expect(find.text('Not suitable for this function'), findsOneWidget);
    expect(find.textContaining('artificial fly'), findsOneWidget);
    expect(find.text('No identification'), findsOneWidget);
    expect(find.text('Recommended flies'), findsNothing);
  });

  testWidgets('fly result shows imitated organisms, AI hints and products', (tester) async {
    final api = FakeApi(identifyResult: FlyIdentification.fromJson(fixtureMap('fly_result.json')));
    await pumpApp(tester, api: api, initialLocation: '/history/abc', locale: const Locale('es'));
    expect(find.text('Woolly Bugger'), findsOneWidget);
    await tester.scrollUntilVisible(find.text('Imita a'), 300);
    expect(find.text('Aeshnidae'), findsOneWidget);
    await tester.scrollUntilVisible(find.text('Sugerencias de la IA (sin verificar)'), 300);
    await tester.scrollUntilVisible(find.text('Dónde comprar'), 300);
    expect(find.text('EXAMPLE Woolly Bugger #8'), findsOneWidget);
  });

  testWidgets('empty catalog shows an empty state', (tester) async {
    await pumpApp(tester, api: FakeApi(), initialLocation: '/catalog');
    expect(find.text('The catalog is empty for now.'), findsOneWidget);
  });

  testWidgets('catalog lists organisms and searches', (tester) async {
    final api = FakeApi(organismPage: CatalogPage.fromJson(fixtureMap('organisms_page.json'), OrganismSummary.fromJson));
    await pumpApp(tester, api: api, initialLocation: '/catalog');
    expect(find.text('Baetis'), findsOneWidget);
    await tester.enterText(find.byKey(const Key('catalog-search')), 'baetis');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();
    expect(api.calls, contains('organisms:baetis:'));
    await tester.tap(find.text('Aquatic insects'));
    await tester.pumpAndSettle();
    expect(api.calls, contains('organisms:baetis:aquatic_insect'));
  });

  testWidgets('fly detail opens products; empty products are explained', (tester) async {
    await pumpApp(tester, api: FakeApi(), initialLocation: '/flies/x');
    expect(find.text('Woolly Bugger'), findsOneWidget);
    // The photo gallery is a second Scrollable; scroll the page itself.
    await tester.scrollUntilVisible(find.byKey(const Key('fly-products')), 300, scrollable: find.byType(Scrollable).first);
    await tester.tap(find.byKey(const Key('fly-products')));
    await tester.pumpAndSettle();
    expect(find.text('No verified products for this pattern yet.'), findsOneWidget);
  });

  testWidgets('product without price says so instead of inventing one', (tester) async {
    final products = listOf(fixture('fly_products.json'), ProductInfo.fromJson);
    final noPrice = ProductInfo.fromJson({...Json.from(fixture('fly_products.json')[0] as Map), 'price': null, 'currency': null});
    await pumpApp(tester, api: FakeApi(products: [...products, noPrice]), initialLocation: '/flies/x/products');
    expect(find.text('Price not available'), findsOneWidget);
    expect(find.textContaining('ARS'), findsOneWidget);
  });

  testWidgets('history lists past identifications', (tester) async {
    final items = listOf(fixture('history.json'), IdentificationSummary.fromJson);
    await pumpApp(tester, api: FakeApi(historyItems: items), initialLocation: '/history');
    expect(find.text('Woolly Bugger'), findsOneWidget);
    expect(find.text('Baetis'), findsOneWidget);
  });

  test('prices keep their own currency', () {
    expect(formatPrice('4500.00', 'ARS', 'es-AR'), contains('ARS'));
    expect(formatPrice('12.5', 'USD', 'en-US'), 'USD 12.50');
  });
}
