import '../core/network/api_failure.dart';
import '../l10n/app_localizations.dart';

/// Maps the backend's stable codes to localized labels. Unknown codes fall back to the
/// raw value so a newer backend never crashes an older app.
extension CodeLabels on AppLocalizations {
  String matchLevel(String code) => switch (code) {
        'high_match' => matchLevel_high_match,
        'moderate_match' => matchLevel_moderate_match,
        'low_match' => matchLevel_low_match,
        'inconclusive' => matchLevel_inconclusive,
        'insufficient_image' => matchLevel_insufficient_image,
        'not_compatible' => matchLevel_not_compatible,
        _ => code,
      };

  String confidence(String code) => switch (code) {
        'high' => confidence_high,
        'moderate' => confidence_moderate,
        'low' => confidence_low,
        'none' => confidence_none,
        _ => code,
      };

  String stage(String code) => switch (code) {
        'egg' => lifeStage_egg,
        'larva' => lifeStage_larva,
        'nymph' => lifeStage_nymph,
        'pupa' => lifeStage_pupa,
        'emerger' => lifeStage_emerger,
        'subimago' => lifeStage_subimago,
        'imago' => lifeStage_imago,
        'adult' => lifeStage_adult,
        'juvenile' => lifeStage_juvenile,
        'other' => lifeStage_other,
        'unknown' => lifeStage_unknown,
        _ => code,
      };

  String rankName(String code) => switch (code) {
        'kingdom' => rank_kingdom,
        'phylum' => rank_phylum,
        'class' => rank_class,
        'subclass' => rank_subclass,
        'order' => rank_order,
        'suborder' => rank_suborder,
        'infraorder' => rank_infraorder,
        'superfamily' => rank_superfamily,
        'family' => rank_family,
        'subfamily' => rank_subfamily,
        'genus' => rank_genus,
        'species' => rank_species,
        'subspecies' => rank_subspecies,
        _ => code,
      };

  /// Label for a taxonomy field returned by the API (kingdom, class_name, order...).
  String taxonomyField(String key) => switch (key) {
        'kingdom' => kingdom,
        'phylum' => phylum,
        'class_name' => className,
        'order' => order,
        'family' => family,
        'genus' => genus,
        'species' => species,
        _ => key,
      };

  String category(String code) => switch (code) {
        'dry_fly' => category_dry_fly,
        'nymph' => category_nymph,
        'emerger' => category_emerger,
        'wet_fly' => category_wet_fly,
        'streamer' => category_streamer,
        'terrestrial' => category_terrestrial,
        'saltwater' => category_saltwater,
        'attractor' => category_attractor,
        'other' => category_other,
        _ => code,
      };

  String matchType(String code) => switch (code) {
        'exact_imitation' => matchType_exact_imitation,
        'general_imitation' => matchType_general_imitation,
        'suggestive_imitation' => matchType_suggestive_imitation,
        'attractor' => matchType_attractor,
        'not_specified' => matchType_not_specified,
        _ => code,
      };

  String compatibility(String code) => switch (code) {
        'high' => compat_high,
        'medium' => compat_medium,
        'low' => compat_low,
        _ => compat_unknown,
      };

  String tier(String code) => switch (code) {
        'biological_same_stage' => tier_biological_same_stage,
        'biological_stage_unknown' => tier_biological_stage_unknown,
        'biological_other_stage' => tier_biological_other_stage,
        'related_taxon' => tier_related_taxon,
        'visual_only' => tier_visual_only,
        _ => code,
      };

  String group(String code) => switch (code) {
        'aquatic_insect' => group_aquatic_insect,
        'terrestrial_insect' => group_terrestrial_insect,
        'crustacean' => group_crustacean,
        'annelid' => group_annelid,
        'mollusc' => group_mollusc,
        'fish' => group_fish,
        _ => group_other,
      };

  String habitatName(String code) => switch (code) {
        'freshwater_running' => habitat_freshwater_running,
        'freshwater_still' => habitat_freshwater_still,
        'estuarine' => habitat_estuarine,
        'marine' => habitat_marine,
        'terrestrial' => habitat_terrestrial,
        _ => code,
      };

  String availability(String code) => switch (code) {
        'in_stock' => availability_in_stock,
        'out_of_stock' => availability_out_of_stock,
        'preorder' => availability_preorder,
        'discontinued' => availability_discontinued,
        _ => availability_unknown,
      };

  String failure(Object error) {
    if (error is! ApiFailure) return errorUnknown;
    return switch (error.kind) {
      FailureKind.network => errorNetwork,
      FailureKind.timeout => errorTimeout,
      FailureKind.rateLimited => errorRateLimited,
      FailureKind.invalidImage => errorInvalidImage,
      FailureKind.tooLarge => errorTooLarge,
      FailureKind.unavailable => errorUnavailable,
      FailureKind.notFound => errorNotFound,
      FailureKind.server => errorServer,
      FailureKind.unknown => errorUnknown,
    };
  }
}
