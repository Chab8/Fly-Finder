import 'json.dart';

class CatalogImage {
  const CatalogImage({required this.url, required this.license, required this.attribution, this.sourceUrl});

  final String url;
  final String license;
  final String attribution;
  final String? sourceUrl;

  factory CatalogImage.fromJson(Json j) =>
      CatalogImage(url: j['url'] as String, license: j['license'] as String, attribution: j['attribution'] as String, sourceUrl: j['source_url'] as String?);
}

class OrganismSummary {
  const OrganismSummary({
    required this.id,
    required this.scientificName,
    required this.taxonomicRank,
    required this.organismGroup,
    this.commonName,
    this.order,
    this.family,
    this.genus,
    this.thumbnailUrl,
    this.isDemo = false,
  });

  final String id;
  final String scientificName;
  final String? commonName;
  final String taxonomicRank;
  final String? order;
  final String? family;
  final String? genus;
  final String organismGroup;
  final String? thumbnailUrl;
  final bool isDemo;

  factory OrganismSummary.fromJson(Json j) => OrganismSummary(
        id: j['id'] as String,
        scientificName: j['scientific_name'] as String,
        commonName: j['common_name'] as String?,
        taxonomicRank: j['taxonomic_rank'] as String,
        order: j['order'] as String?,
        family: j['family'] as String?,
        genus: j['genus'] as String?,
        organismGroup: j['organism_group'] as String,
        thumbnailUrl: j['thumbnail_url'] as String?,
        isDemo: j['is_demo'] as bool? ?? false,
      );
}

class FlyPatternSummary {
  const FlyPatternSummary({
    required this.id,
    required this.slug,
    required this.name,
    required this.category,
    required this.imitationType,
    this.hookSizeMin,
    this.hookSizeMax,
    this.colors = const [],
    this.thumbnailUrl,
    this.isDemo = false,
  });

  final String id;
  final String slug;
  final String name;
  final String category;
  final String imitationType;
  final String? hookSizeMin;
  final String? hookSizeMax;
  final List<String> colors;
  final String? thumbnailUrl;
  final bool isDemo;

  factory FlyPatternSummary.fromJson(Json j) => FlyPatternSummary(
        id: j['id'] as String,
        slug: j['slug'] as String,
        name: j['name'] as String,
        category: j['category'] as String,
        imitationType: j['imitation_type'] as String,
        hookSizeMin: j['hook_size_min'] as String?,
        hookSizeMax: j['hook_size_max'] as String?,
        colors: stringsOf(j['colors']),
        thumbnailUrl: j['thumbnail_url'] as String?,
        isDemo: j['is_demo'] as bool? ?? false,
      );
}

/// A documented organism <-> fly relationship (fly_organism_matches).
class Relation {
  const Relation({
    required this.lifeStage,
    required this.matchType,
    required this.biologicalCompatibility,
    required this.expertVerified,
    this.verificationSource,
    this.notes,
    this.fly,
    this.organism,
  });

  final String lifeStage;
  final String matchType;
  final String biologicalCompatibility;
  final bool expertVerified;
  final String? verificationSource;
  final String? notes;
  final FlyPatternSummary? fly;
  final OrganismSummary? organism;

  factory Relation.fromJson(Json j) => Relation(
        lifeStage: j['life_stage'] as String,
        matchType: j['match_type'] as String,
        biologicalCompatibility: j['biological_compatibility'] as String,
        expertVerified: j['expert_verified'] as bool? ?? false,
        verificationSource: j['verification_source'] as String?,
        notes: j['notes'] as String?,
        fly: objectOf(j['fly'], FlyPatternSummary.fromJson),
        organism: objectOf(j['organism'], OrganismSummary.fromJson),
      );
}

class OrganismDetail {
  const OrganismDetail({
    required this.summary,
    required this.taxonomy,
    required this.habitats,
    required this.lifeStages,
    required this.images,
    required this.imitatedBy,
    required this.verificationStatus,
    this.commonNames = const [],
    this.gbifTaxonId,
    this.description,
    this.fishingNotes,
    this.distribution,
  });

  final OrganismSummary summary;
  final Map<String, String?> taxonomy;
  final List<({String language, String name})> commonNames;
  final List<String> habitats;
  final List<String> lifeStages;
  final List<CatalogImage> images;
  final List<Relation> imitatedBy;
  final String verificationStatus;
  final int? gbifTaxonId;
  final String? description;
  final String? fishingNotes;
  final String? distribution;

  factory OrganismDetail.fromJson(Json j) {
    final taxonomy = Json.from(j['taxonomy'] as Map? ?? const {});
    return OrganismDetail(
      summary: OrganismSummary.fromJson(j),
      taxonomy: {for (final key in ['kingdom', 'phylum', 'class_name', 'order', 'family', 'genus', 'species']) key: taxonomy[key] as String?},
      commonNames: listOf(j['common_names'], (n) => (language: n['language'] as String, name: n['name'] as String)),
      habitats: stringsOf(j['habitats']),
      lifeStages: stringsOf(j['life_stages']),
      images: listOf(j['images'], CatalogImage.fromJson),
      imitatedBy: listOf(j['imitated_by'], Relation.fromJson),
      verificationStatus: j['verification_status'] as String? ?? 'unverified',
      gbifTaxonId: j['gbif_taxon_id'] as int?,
      description: j['description'] as String?,
      fishingNotes: j['fishing_notes'] as String?,
      distribution: j['geographic_distribution'] as String?,
    );
  }
}

class FlyMaterial {
  const FlyMaterial(this.component, this.material);
  final String component;
  final String material;
}

class FlyVariant {
  const FlyVariant(this.name, [this.description]);
  final String name;
  final String? description;

  factory FlyVariant.fromJson(Json j) => FlyVariant(j['name'] as String, j['description'] as String?);
}

class FlyPatternDetail {
  const FlyPatternDetail({
    required this.summary,
    required this.alternateNames,
    required this.materials,
    required this.variants,
    required this.fishingEnvironments,
    required this.images,
    required this.imitates,
    required this.productCount,
    required this.verificationStatus,
    this.description,
    this.usageNotes,
    this.difficulty,
  });

  final FlyPatternSummary summary;
  final List<String> alternateNames;
  final List<FlyMaterial> materials;
  final List<FlyVariant> variants;
  final List<String> fishingEnvironments;
  final List<CatalogImage> images;
  final List<Relation> imitates;
  final int productCount;
  final String verificationStatus;
  final String? description;
  final String? usageNotes;
  final String? difficulty;

  factory FlyPatternDetail.fromJson(Json j) => FlyPatternDetail(
        summary: FlyPatternSummary.fromJson(j),
        alternateNames: stringsOf(j['alternate_names']),
        materials: listOf(j['materials'], (m) => FlyMaterial(m['component'] as String, m['material'] as String)),
        variants: listOf(j['variants'], FlyVariant.fromJson),
        fishingEnvironments: stringsOf(j['fishing_environments']),
        images: listOf(j['images'], CatalogImage.fromJson),
        imitates: listOf(j['imitates'], Relation.fromJson),
        productCount: j['product_count'] as int? ?? 0,
        verificationStatus: j['verification_status'] as String? ?? 'unverified',
        description: j['description'] as String?,
        usageNotes: j['usage_notes'] as String?,
        difficulty: j['difficulty'] as String?,
      );
}

class CatalogPage<T> {
  const CatalogPage(this.items, this.total);
  final List<T> items;
  final int total;

  factory CatalogPage.fromJson(Json j, T Function(Json) parse) => CatalogPage(listOf(j['items'], parse), j['total'] as int? ?? 0);
}
