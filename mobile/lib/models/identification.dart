import 'catalog.dart';
import 'commerce.dart';
import 'json.dart';

enum IdentifyMode {
  organism,
  fly;

  static IdentifyMode parse(String value) => value == 'fly' ? IdentifyMode.fly : IdentifyMode.organism;
}

class Notice {
  const Notice(this.code, this.message);
  final String code;
  final String message;

  factory Notice.fromJson(Json j) => Notice(j['code'] as String, j['message'] as String);
}

class AnalysisInfo {
  const AnalysisInfo({required this.aiAvailable, required this.embeddingsAvailable, required this.isDemo, this.aiModel});
  final bool aiAvailable;
  final bool embeddingsAvailable;
  final bool isDemo;
  final String? aiModel;

  factory AnalysisInfo.fromJson(Json j) => AnalysisInfo(
        aiAvailable: j['ai_available'] as bool? ?? false,
        embeddingsAvailable: j['embeddings_available'] as bool? ?? false,
        isDemo: j['is_demo'] as bool? ?? false,
        aiModel: j['ai_model'] as String?,
      );
}

class EvidenceSource {
  const EvidenceSource(this.name, this.detail, this.url);
  final String name;
  final String? detail;
  final String? url;

  factory EvidenceSource.fromJson(Json j) => EvidenceSource(j['name'] as String, j['detail'] as String?, j['url'] as String?);
}

/// Fields shared by both identification responses.
abstract class IdentificationResult {
  const IdentificationResult({
    required this.matchLevel,
    required this.warnings,
    required this.sources,
    required this.analysis,
    this.identificationId,
  });

  final String? identificationId;
  final String matchLevel;
  final List<Notice> warnings;
  final List<EvidenceSource> sources;
  final AnalysisInfo analysis;

  IdentifyMode get mode;
}

class OrganismCandidate {
  const OrganismCandidate({
    required this.scientificName,
    required this.taxonomicRank,
    required this.aiConfidence,
    required this.taxonomyVerified,
    required this.inCatalog,
    this.commonName,
    this.order,
    this.family,
    this.genus,
    this.visualEvidence,
    this.catalogOrganism,
    this.gbifUrl,
  });

  final String scientificName;
  final String taxonomicRank;
  final String? commonName;
  final String? order;
  final String? family;
  final String? genus;
  final String aiConfidence;
  final String? visualEvidence;
  final bool taxonomyVerified;
  final bool inCatalog;
  final OrganismSummary? catalogOrganism;
  final String? gbifUrl;

  factory OrganismCandidate.fromJson(Json j) => OrganismCandidate(
        scientificName: j['scientific_name'] as String,
        taxonomicRank: j['taxonomic_rank'] as String,
        commonName: j['common_name'] as String?,
        order: j['order'] as String?,
        family: j['family'] as String?,
        genus: j['genus'] as String?,
        aiConfidence: j['ai_confidence'] as String,
        visualEvidence: j['visual_evidence'] as String?,
        taxonomyVerified: j['taxonomy_verified'] as bool? ?? false,
        inCatalog: j['in_catalog'] as bool? ?? false,
        catalogOrganism: objectOf(j['catalog_organism'], OrganismSummary.fromJson),
        gbifUrl: (j['taxonomy'] as Map?)?['url'] as String?,
      );
}

class FlyRecommendation {
  const FlyRecommendation({
    required this.fly,
    required this.tier,
    required this.expertVerified,
    required this.rankingScore,
    required this.reasons,
    this.matchedOrganism,
    this.lifeStage,
    this.matchType,
    this.biologicalCompatibility,
    this.visualSimilarity,
  });

  final FlyPatternSummary fly;
  final String tier;
  final OrganismSummary? matchedOrganism;
  final String? lifeStage;
  final String? matchType;
  final String? biologicalCompatibility;
  final bool expertVerified;
  final double? visualSimilarity;
  final double rankingScore;
  final List<String> reasons;

  factory FlyRecommendation.fromJson(Json j) => FlyRecommendation(
        fly: FlyPatternSummary.fromJson(Json.from(j['fly'] as Map)),
        tier: j['tier'] as String,
        matchedOrganism: objectOf(j['matched_organism'], OrganismSummary.fromJson),
        lifeStage: j['life_stage'] as String?,
        matchType: j['match_type'] as String?,
        biologicalCompatibility: j['biological_compatibility'] as String?,
        expertVerified: j['expert_verified'] as bool? ?? false,
        visualSimilarity: doubleOf(j['visual_similarity']),
        rankingScore: doubleOf(j['ranking_score']) ?? 0,
        reasons: stringsOf(j['reasons']),
      );
}

class OrganismIdentification extends IdentificationResult {
  const OrganismIdentification({
    required super.matchLevel,
    required super.warnings,
    required super.sources,
    required super.analysis,
    required this.alternatives,
    required this.lifeStage,
    required this.lifeStageConfidence,
    required this.recommendations,
    required this.similarOrganisms,
    super.identificationId,
    this.primary,
    this.colors = const [],
    this.features = const [],
    this.estimatedLengthMm,
    this.sizeReference,
  });

  final OrganismCandidate? primary;
  final List<OrganismCandidate> alternatives;
  final String lifeStage;
  final String lifeStageConfidence;
  final List<String> colors;
  final List<String> features;
  final double? estimatedLengthMm;
  final String? sizeReference;
  final List<FlyRecommendation> recommendations;
  final List<(OrganismSummary, double)> similarOrganisms;

  @override
  IdentifyMode get mode => IdentifyMode.organism;

  factory OrganismIdentification.fromJson(Json j) {
    final features = Json.from(j['visual_features'] as Map? ?? const {});
    return OrganismIdentification(
      identificationId: j['identification_id'] as String?,
      matchLevel: j['match_level'] as String,
      warnings: listOf(j['warnings'], Notice.fromJson),
      sources: listOf(j['sources'], EvidenceSource.fromJson),
      analysis: AnalysisInfo.fromJson(Json.from(j['analysis'] as Map? ?? const {})),
      primary: objectOf(j['primary'], OrganismCandidate.fromJson),
      alternatives: listOf(j['alternatives'], OrganismCandidate.fromJson),
      lifeStage: j['life_stage'] as String? ?? 'unknown',
      lifeStageConfidence: j['life_stage_confidence'] as String? ?? 'none',
      colors: stringsOf(features['colors']),
      features: stringsOf(features['morphological_features']),
      estimatedLengthMm: doubleOf(features['estimated_length_mm']),
      sizeReference: features['size_reference'] as String?,
      recommendations: listOf(j['recommendations'], FlyRecommendation.fromJson),
      similarOrganisms: listOf(
        j['visually_similar_organisms'],
        (s) => (OrganismSummary.fromJson(Json.from(s['organism'] as Map)), doubleOf(s['visual_similarity']) ?? 0),
      ),
    );
  }
}

class FlyCandidate {
  const FlyCandidate({required this.patternName, required this.inCatalog, required this.evidence, this.fly, this.aiConfidence, this.visualSimilarity});

  final String patternName;
  final FlyPatternSummary? fly;
  final bool inCatalog;
  final String? aiConfidence;
  final double? visualSimilarity;
  final List<String> evidence;

  factory FlyCandidate.fromJson(Json j) => FlyCandidate(
        patternName: j['pattern_name'] as String,
        fly: objectOf(j['fly'], FlyPatternSummary.fromJson),
        inCatalog: j['in_catalog'] as bool? ?? false,
        aiConfidence: j['ai_confidence'] as String?,
        visualSimilarity: doubleOf(j['visual_similarity']),
        evidence: stringsOf(j['evidence']),
      );
}

class FlyIdentification extends IdentificationResult {
  const FlyIdentification({
    required super.matchLevel,
    required super.warnings,
    required super.sources,
    required super.analysis,
    required this.alternatives,
    required this.imitates,
    required this.aiHints,
    required this.variants,
    required this.products,
    super.identificationId,
    this.primary,
    this.category,
    this.isAttractorLikely = false,
    this.features = const [],
    this.colors = const [],
  });

  final FlyCandidate? primary;
  final List<FlyCandidate> alternatives;
  final String? category;
  final bool isAttractorLikely;
  final List<String> features;
  final List<String> colors;
  final List<Relation> imitates;
  final List<(String group, String stage, String confidence)> aiHints;
  final List<FlyVariant> variants;
  final List<ProductInfo> products;

  @override
  IdentifyMode get mode => IdentifyMode.fly;

  factory FlyIdentification.fromJson(Json j) {
    final f = Json.from(j['features'] as Map? ?? const {});
    final featureLines = <String>[
      for (final key in ['silhouette', 'body_description', 'wing_description', 'hackle_description'])
        if (f[key] is String && (f[key] as String).isNotEmpty) f[key] as String,
      ...stringsOf(f['visible_materials']),
    ];
    return FlyIdentification(
      identificationId: j['identification_id'] as String?,
      matchLevel: j['match_level'] as String,
      warnings: listOf(j['warnings'], Notice.fromJson),
      sources: listOf(j['sources'], EvidenceSource.fromJson),
      analysis: AnalysisInfo.fromJson(Json.from(j['analysis'] as Map? ?? const {})),
      primary: objectOf(j['primary'], FlyCandidate.fromJson),
      alternatives: listOf(j['alternatives'], FlyCandidate.fromJson),
      category: j['category'] as String?,
      isAttractorLikely: j['is_attractor_likely'] as bool? ?? false,
      features: featureLines,
      colors: stringsOf(f['colors']),
      imitates: listOf(j['imitates'], Relation.fromJson),
      aiHints: listOf(j['ai_imitation_hints'], (h) => (h['organism_group'] as String, h['life_stage'] as String, h['ai_confidence'] as String)),
      variants: listOf(j['variants'], FlyVariant.fromJson),
      products: listOf(j['products'], ProductInfo.fromJson),
    );
  }
}

class IdentificationSummary {
  const IdentificationSummary({required this.id, required this.mode, required this.createdAt, required this.matchLevel, this.primaryLabel, this.isDemo = false});

  final String id;
  final IdentifyMode mode;
  final DateTime createdAt;
  final String matchLevel;
  final String? primaryLabel;
  final bool isDemo;

  factory IdentificationSummary.fromJson(Json j) => IdentificationSummary(
        id: j['id'] as String,
        mode: IdentifyMode.parse(j['kind'] as String),
        createdAt: DateTime.parse(j['created_at'] as String),
        matchLevel: j['match_level'] as String,
        primaryLabel: j['primary_label'] as String?,
        isDemo: j['is_demo'] as bool? ?? false,
      );
}

IdentificationResult parseIdentification(Json json) =>
    json['kind'] == 'fly' ? FlyIdentification.fromJson(json) : OrganismIdentification.fromJson(json);
