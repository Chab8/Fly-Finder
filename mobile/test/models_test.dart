import 'package:flutter_test/flutter_test.dart';
import 'package:fly_finder/models/catalog.dart';
import 'package:fly_finder/models/commerce.dart';
import 'package:fly_finder/models/identification.dart';
import 'package:fly_finder/models/json.dart';

import 'helpers.dart';

void main() {
  test('organism identification parses the real API response', () {
    final result = OrganismIdentification.fromJson(fixtureMap('organism_result.json'));
    expect(result.matchLevel, 'high_match');
    expect(result.primary!.scientificName, 'Baetis');
    expect(result.primary!.taxonomyVerified, isTrue);
    expect(result.alternatives.single.scientificName, 'Heptageniidae');
    expect(result.lifeStage, 'nymph');
    expect(result.recommendations, isNotEmpty);
    expect(result.recommendations.first.tier, 'biological_same_stage');
    expect(result.recommendations.first.reasons, isNotEmpty);
    expect(result.warnings.map((w) => w.code), contains('relations_unverified'));
  });

  test('fly identification parses products with currency', () {
    final result = FlyIdentification.fromJson(fixtureMap('fly_result.json'));
    expect(result.primary!.fly!.slug, 'woolly-bugger');
    expect(result.imitates, isNotEmpty);
    expect(result.aiHints.single.$1, 'Hirudinea');
    expect(result.products.single.price, '4500.00');
    expect(result.products.single.currency, 'ARS');
  });

  test('parseIdentification dispatches on kind', () {
    expect(parseIdentification(fixtureMap('fly_result.json')), isA<FlyIdentification>());
    expect(parseIdentification(fixtureMap('organism_not_compatible.json')), isA<OrganismIdentification>());
  });

  test('catalog and commerce payloads parse', () {
    final page = CatalogPage.fromJson(fixtureMap('organisms_page.json'), OrganismSummary.fromJson);
    expect(page.items.first.scientificName, 'Baetis');
    final detail = OrganismDetail.fromJson(fixtureMap('organism_detail.json'));
    expect(detail.imitatedBy, isNotEmpty);
    expect(detail.gbifTaxonId, isNotNull);
    final fly = FlyPatternDetail.fromJson(fixtureMap('fly_detail.json'));
    expect(fly.materials, isNotEmpty);
    expect(fly.productCount, 1);
    final products = listOf(fixture('fly_products.json'), ProductInfo.fromJson);
    expect(products.single.store.currency, 'ARS');
    final history = listOf(fixture('history.json'), IdentificationSummary.fromJson);
    expect(history.map((h) => h.mode), containsAll([IdentifyMode.organism, IdentifyMode.fly]));
  });
}
