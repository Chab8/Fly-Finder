// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get homeTagline =>
      'Match what\'s hatching with what\'s in your fly box.';

  @override
  String get identifyOrganismTitle => 'Identify an organism';

  @override
  String get identifyOrganismSubtitle =>
      'Photograph an insect, crustacean or baitfish and find flies that imitate it.';

  @override
  String get identifyFlyTitle => 'Identify a fly';

  @override
  String get identifyFlySubtitle =>
      'Photograph an artificial fly and learn what it imitates.';

  @override
  String get catalogTitle => 'Catalog';

  @override
  String get catalogSubtitle => 'Organisms and fly patterns';

  @override
  String get historyTitle => 'History';

  @override
  String get historySubtitle => 'Your recent identifications';

  @override
  String get demoBanner => 'DEMO MODE · fictional data, no real identification';

  @override
  String get captureHintOrganism =>
      'Fill the frame with the organism, in focus and well lit. A side view helps.';

  @override
  String get captureHintFly =>
      'Place the fly on a plain background and photograph it from the side.';

  @override
  String get takePhoto => 'Take photo';

  @override
  String get chooseFromGallery => 'Choose from gallery';

  @override
  String get changePhoto => 'Change photo';

  @override
  String get cancel => 'Cancel';

  @override
  String get analyze => 'Analyze photo';

  @override
  String get noPhotoSelected => 'No photo selected yet';

  @override
  String get permissionDenied =>
      'Permission to use the camera or photos was denied. You can enable it in Settings.';

  @override
  String imageTooLargeLocal(int limit) {
    return 'This photo is larger than $limit MB. Please choose a smaller one.';
  }

  @override
  String get unsupportedFormatLocal =>
      'Unsupported file type. Use JPEG, PNG, WEBP or HEIC.';

  @override
  String get phaseUploading => 'Sending photo';

  @override
  String get phaseAnalyzing => 'Analyzing on the server';

  @override
  String get analysisNote => 'AI analysis can take up to a minute.';

  @override
  String get resultOrganismTitle => 'Organism result';

  @override
  String get resultFlyTitle => 'Fly result';

  @override
  String get primaryIdentification => 'Most likely';

  @override
  String get alternatives => 'Alternatives';

  @override
  String get noIdentification => 'No identification';

  @override
  String get scientificName => 'Scientific name';

  @override
  String get commonName => 'Common name';

  @override
  String get order => 'Order';

  @override
  String get family => 'Family';

  @override
  String get genus => 'Genus';

  @override
  String get rank => 'Rank';

  @override
  String get lifeStage => 'Life stage';

  @override
  String get characteristics => 'Visible features';

  @override
  String get colors => 'Colours';

  @override
  String estimatedLength(String mm, String reference) {
    return 'Estimated length: $mm mm ($reference)';
  }

  @override
  String get certainty => 'Certainty';

  @override
  String get certaintyExplanation =>
      'Certainty is a qualitative level from documented rules, not a percentage.';

  @override
  String get recommendedFlies => 'Recommended flies';

  @override
  String get noRecommendations =>
      'Our catalog does not document flies for this organism yet.';

  @override
  String visualSimilarity(String value) {
    return 'Visual similarity $value';
  }

  @override
  String get notAProbability =>
      'Similarity and ranking scores are not probabilities.';

  @override
  String get similarOrganisms => 'Visually similar in the catalog';

  @override
  String get imitates => 'Imitates';

  @override
  String get imitatesNothingDocumented =>
      'No documented organism for this pattern. It may be an attractor or general pattern.';

  @override
  String get aiSuggestions => 'AI suggestions (not verified)';

  @override
  String get variants => 'Variants';

  @override
  String get products => 'Where to buy';

  @override
  String get noProducts => 'No verified products for this pattern yet.';

  @override
  String get viewProducts => 'View products';

  @override
  String get expertVerified => 'Expert verified';

  @override
  String get notExpertVerified => 'Not yet expert verified';

  @override
  String get inCatalog => 'In catalog';

  @override
  String get notInCatalog => 'Not in catalog';

  @override
  String get taxonomyVerified => 'Name checked in GBIF';

  @override
  String get sources => 'Sources';

  @override
  String get warnings => 'Notes';

  @override
  String get retry => 'Retry';

  @override
  String get backHome => 'Back to home';

  @override
  String get newPhoto => 'New photo';

  @override
  String get openPattern => 'Open pattern';

  @override
  String get openOrganism => 'Open organism';

  @override
  String get organismsTab => 'Organisms';

  @override
  String get fliesTab => 'Flies';

  @override
  String get searchHint => 'Search by name';

  @override
  String get filterAll => 'All';

  @override
  String get emptyCatalog => 'The catalog is empty for now.';

  @override
  String get emptySearch => 'Nothing matches your search.';

  @override
  String get noImages => 'No licensed photos yet';

  @override
  String photoCredit(String attribution, String license) {
    return 'Photo: $attribution · $license';
  }

  @override
  String get taxonomy => 'Taxonomy';

  @override
  String get habitat => 'Habitat';

  @override
  String get lifeStages => 'Life stages';

  @override
  String get distribution => 'Distribution';

  @override
  String get description => 'Description';

  @override
  String get fishingNotes => 'For anglers';

  @override
  String get materials => 'Materials';

  @override
  String get hookSizes => 'Hook sizes';

  @override
  String hookRange(String max, String min) {
    return '#$max – #$min';
  }

  @override
  String get imitatedBy => 'Imitated by';

  @override
  String get dataReviewNote => 'Catalog data pending expert review.';

  @override
  String get gbifLink => 'View on GBIF';

  @override
  String get productsTitle => 'Products';

  @override
  String get priceNotAvailable => 'Price not available';

  @override
  String lastVerified(String date) {
    return 'Checked $date';
  }

  @override
  String get shipsToYou => 'Ships to your country';

  @override
  String get openStore => 'Open store page';

  @override
  String get cannotOpenLink => 'Could not open the link.';

  @override
  String get historyEmpty => 'Your identifications will appear here.';

  @override
  String get errorNetwork =>
      'No connection to the server. Check your internet connection.';

  @override
  String get errorTimeout =>
      'The server took too long to answer. Please try again.';

  @override
  String get errorServer => 'The server could not complete the request.';

  @override
  String get errorRateLimited =>
      'Too many attempts. Wait a minute and try again.';

  @override
  String get errorInvalidImage =>
      'The photo could not be read. Try another one.';

  @override
  String get errorTooLarge => 'The photo is too large.';

  @override
  String get errorUnavailable =>
      'Image analysis is temporarily unavailable. Please try again later.';

  @override
  String get errorNotFound => 'Not found.';

  @override
  String get errorUnknown => 'Something went wrong.';

  @override
  String get matchLevel_high_match => 'High match';

  @override
  String get matchLevel_moderate_match => 'Moderate match';

  @override
  String get matchLevel_low_match => 'Low match';

  @override
  String get matchLevel_inconclusive => 'Inconclusive';

  @override
  String get matchLevel_insufficient_image => 'Photo not good enough';

  @override
  String get matchLevel_not_compatible => 'Not suitable for this function';

  @override
  String aiConfidence(String level) {
    return 'AI confidence: $level';
  }

  @override
  String get confidence_high => 'high';

  @override
  String get confidence_moderate => 'moderate';

  @override
  String get confidence_low => 'low';

  @override
  String get confidence_none => 'none';

  @override
  String get lifeStage_egg => 'Egg';

  @override
  String get lifeStage_larva => 'Larva';

  @override
  String get lifeStage_nymph => 'Nymph';

  @override
  String get lifeStage_pupa => 'Pupa';

  @override
  String get lifeStage_emerger => 'Emerger';

  @override
  String get lifeStage_subimago => 'Dun (subimago)';

  @override
  String get lifeStage_imago => 'Spinner (imago)';

  @override
  String get lifeStage_adult => 'Adult';

  @override
  String get lifeStage_juvenile => 'Juvenile';

  @override
  String get lifeStage_other => 'Other';

  @override
  String get lifeStage_unknown => 'Unknown';

  @override
  String get category_dry_fly => 'Dry fly';

  @override
  String get category_nymph => 'Nymph';

  @override
  String get category_emerger => 'Emerger';

  @override
  String get category_wet_fly => 'Wet fly';

  @override
  String get category_streamer => 'Streamer';

  @override
  String get category_terrestrial => 'Terrestrial';

  @override
  String get category_saltwater => 'Saltwater';

  @override
  String get category_attractor => 'Attractor';

  @override
  String get category_other => 'Other';

  @override
  String get matchType_exact_imitation => 'Exact imitation';

  @override
  String get matchType_general_imitation => 'General imitation';

  @override
  String get matchType_suggestive_imitation => 'Suggestive imitation';

  @override
  String get matchType_attractor => 'Attractor';

  @override
  String get matchType_not_specified => 'Not specified';

  @override
  String get compat_high => 'High biological compatibility';

  @override
  String get compat_medium => 'Medium biological compatibility';

  @override
  String get compat_low => 'Low biological compatibility';

  @override
  String get compat_unknown => 'Unknown biological compatibility';

  @override
  String get tier_biological_same_stage => 'Documented for this life stage';

  @override
  String get tier_biological_stage_unknown =>
      'Documented (stage not determined)';

  @override
  String get tier_biological_other_stage => 'Documented for another life stage';

  @override
  String get tier_related_taxon => 'Documented for a relative';

  @override
  String get tier_visual_only => 'Only visually similar';

  @override
  String get group_aquatic_insect => 'Aquatic insects';

  @override
  String get group_terrestrial_insect => 'Terrestrial insects';

  @override
  String get group_crustacean => 'Crustaceans';

  @override
  String get group_annelid => 'Worms and leeches';

  @override
  String get group_mollusc => 'Molluscs';

  @override
  String get group_fish => 'Fish';

  @override
  String get group_other => 'Other';

  @override
  String get habitat_freshwater_running => 'Running water';

  @override
  String get habitat_freshwater_still => 'Still water';

  @override
  String get habitat_estuarine => 'Estuaries';

  @override
  String get habitat_marine => 'Sea';

  @override
  String get habitat_terrestrial => 'Land';

  @override
  String get availability_in_stock => 'In stock';

  @override
  String get availability_out_of_stock => 'Out of stock';

  @override
  String get availability_preorder => 'Pre-order';

  @override
  String get availability_discontinued => 'Discontinued';

  @override
  String get availability_unknown => 'Availability unknown';

  @override
  String get kind_organism => 'Organism';

  @override
  String get kind_fly => 'Fly';

  @override
  String get kingdom => 'Kingdom';

  @override
  String get phylum => 'Phylum';

  @override
  String get className => 'Class';

  @override
  String get species => 'Species';

  @override
  String get rank_kingdom => 'kingdom';

  @override
  String get rank_phylum => 'phylum';

  @override
  String get rank_class => 'class';

  @override
  String get rank_subclass => 'subclass';

  @override
  String get rank_order => 'order';

  @override
  String get rank_suborder => 'suborder';

  @override
  String get rank_infraorder => 'infraorder';

  @override
  String get rank_superfamily => 'superfamily';

  @override
  String get rank_family => 'family';

  @override
  String get rank_subfamily => 'subfamily';

  @override
  String get rank_genus => 'genus';

  @override
  String get rank_species => 'species';

  @override
  String get rank_subspecies => 'subspecies';
}
