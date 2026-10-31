import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_es.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('es'),
  ];

  /// No description provided for @homeTagline.
  ///
  /// In en, this message translates to:
  /// **'Match what\'s hatching with what\'s in your fly box.'**
  String get homeTagline;

  /// No description provided for @identifyOrganismTitle.
  ///
  /// In en, this message translates to:
  /// **'Identify an organism'**
  String get identifyOrganismTitle;

  /// No description provided for @identifyOrganismSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Photograph an insect, crustacean or baitfish and find flies that imitate it.'**
  String get identifyOrganismSubtitle;

  /// No description provided for @identifyFlyTitle.
  ///
  /// In en, this message translates to:
  /// **'Identify a fly'**
  String get identifyFlyTitle;

  /// No description provided for @identifyFlySubtitle.
  ///
  /// In en, this message translates to:
  /// **'Photograph an artificial fly and learn what it imitates.'**
  String get identifyFlySubtitle;

  /// No description provided for @catalogTitle.
  ///
  /// In en, this message translates to:
  /// **'Catalog'**
  String get catalogTitle;

  /// No description provided for @catalogSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Organisms and fly patterns'**
  String get catalogSubtitle;

  /// No description provided for @historyTitle.
  ///
  /// In en, this message translates to:
  /// **'History'**
  String get historyTitle;

  /// No description provided for @historySubtitle.
  ///
  /// In en, this message translates to:
  /// **'Your recent identifications'**
  String get historySubtitle;

  /// No description provided for @demoBanner.
  ///
  /// In en, this message translates to:
  /// **'DEMO MODE · fictional data, no real identification'**
  String get demoBanner;

  /// No description provided for @captureHintOrganism.
  ///
  /// In en, this message translates to:
  /// **'Fill the frame with the organism, in focus and well lit. A side view helps.'**
  String get captureHintOrganism;

  /// No description provided for @captureHintFly.
  ///
  /// In en, this message translates to:
  /// **'Place the fly on a plain background and photograph it from the side.'**
  String get captureHintFly;

  /// No description provided for @takePhoto.
  ///
  /// In en, this message translates to:
  /// **'Take photo'**
  String get takePhoto;

  /// No description provided for @chooseFromGallery.
  ///
  /// In en, this message translates to:
  /// **'Choose from gallery'**
  String get chooseFromGallery;

  /// No description provided for @changePhoto.
  ///
  /// In en, this message translates to:
  /// **'Change photo'**
  String get changePhoto;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @analyze.
  ///
  /// In en, this message translates to:
  /// **'Analyze photo'**
  String get analyze;

  /// No description provided for @noPhotoSelected.
  ///
  /// In en, this message translates to:
  /// **'No photo selected yet'**
  String get noPhotoSelected;

  /// No description provided for @permissionDenied.
  ///
  /// In en, this message translates to:
  /// **'Permission to use the camera or photos was denied. You can enable it in Settings.'**
  String get permissionDenied;

  /// No description provided for @imageTooLargeLocal.
  ///
  /// In en, this message translates to:
  /// **'This photo is larger than {limit} MB. Please choose a smaller one.'**
  String imageTooLargeLocal(int limit);

  /// No description provided for @unsupportedFormatLocal.
  ///
  /// In en, this message translates to:
  /// **'Unsupported file type. Use JPEG, PNG, WEBP or HEIC.'**
  String get unsupportedFormatLocal;

  /// No description provided for @phaseUploading.
  ///
  /// In en, this message translates to:
  /// **'Sending photo'**
  String get phaseUploading;

  /// No description provided for @phaseAnalyzing.
  ///
  /// In en, this message translates to:
  /// **'Analyzing on the server'**
  String get phaseAnalyzing;

  /// No description provided for @analysisNote.
  ///
  /// In en, this message translates to:
  /// **'AI analysis can take up to a minute.'**
  String get analysisNote;

  /// No description provided for @resultOrganismTitle.
  ///
  /// In en, this message translates to:
  /// **'Organism result'**
  String get resultOrganismTitle;

  /// No description provided for @resultFlyTitle.
  ///
  /// In en, this message translates to:
  /// **'Fly result'**
  String get resultFlyTitle;

  /// No description provided for @primaryIdentification.
  ///
  /// In en, this message translates to:
  /// **'Most likely'**
  String get primaryIdentification;

  /// No description provided for @alternatives.
  ///
  /// In en, this message translates to:
  /// **'Alternatives'**
  String get alternatives;

  /// No description provided for @noIdentification.
  ///
  /// In en, this message translates to:
  /// **'No identification'**
  String get noIdentification;

  /// No description provided for @scientificName.
  ///
  /// In en, this message translates to:
  /// **'Scientific name'**
  String get scientificName;

  /// No description provided for @commonName.
  ///
  /// In en, this message translates to:
  /// **'Common name'**
  String get commonName;

  /// No description provided for @order.
  ///
  /// In en, this message translates to:
  /// **'Order'**
  String get order;

  /// No description provided for @family.
  ///
  /// In en, this message translates to:
  /// **'Family'**
  String get family;

  /// No description provided for @genus.
  ///
  /// In en, this message translates to:
  /// **'Genus'**
  String get genus;

  /// No description provided for @rank.
  ///
  /// In en, this message translates to:
  /// **'Rank'**
  String get rank;

  /// No description provided for @lifeStage.
  ///
  /// In en, this message translates to:
  /// **'Life stage'**
  String get lifeStage;

  /// No description provided for @characteristics.
  ///
  /// In en, this message translates to:
  /// **'Visible features'**
  String get characteristics;

  /// No description provided for @colors.
  ///
  /// In en, this message translates to:
  /// **'Colours'**
  String get colors;

  /// No description provided for @estimatedLength.
  ///
  /// In en, this message translates to:
  /// **'Estimated length: {mm} mm ({reference})'**
  String estimatedLength(String mm, String reference);

  /// No description provided for @certainty.
  ///
  /// In en, this message translates to:
  /// **'Certainty'**
  String get certainty;

  /// No description provided for @certaintyExplanation.
  ///
  /// In en, this message translates to:
  /// **'Certainty is a qualitative level from documented rules, not a percentage.'**
  String get certaintyExplanation;

  /// No description provided for @recommendedFlies.
  ///
  /// In en, this message translates to:
  /// **'Recommended flies'**
  String get recommendedFlies;

  /// No description provided for @noRecommendations.
  ///
  /// In en, this message translates to:
  /// **'Our catalog does not document flies for this organism yet.'**
  String get noRecommendations;

  /// No description provided for @visualSimilarity.
  ///
  /// In en, this message translates to:
  /// **'Visual similarity {value}'**
  String visualSimilarity(String value);

  /// No description provided for @notAProbability.
  ///
  /// In en, this message translates to:
  /// **'Similarity and ranking scores are not probabilities.'**
  String get notAProbability;

  /// No description provided for @similarOrganisms.
  ///
  /// In en, this message translates to:
  /// **'Visually similar in the catalog'**
  String get similarOrganisms;

  /// No description provided for @imitates.
  ///
  /// In en, this message translates to:
  /// **'Imitates'**
  String get imitates;

  /// No description provided for @imitatesNothingDocumented.
  ///
  /// In en, this message translates to:
  /// **'No documented organism for this pattern. It may be an attractor or general pattern.'**
  String get imitatesNothingDocumented;

  /// No description provided for @aiSuggestions.
  ///
  /// In en, this message translates to:
  /// **'AI suggestions (not verified)'**
  String get aiSuggestions;

  /// No description provided for @variants.
  ///
  /// In en, this message translates to:
  /// **'Variants'**
  String get variants;

  /// No description provided for @products.
  ///
  /// In en, this message translates to:
  /// **'Where to buy'**
  String get products;

  /// No description provided for @noProducts.
  ///
  /// In en, this message translates to:
  /// **'No verified products for this pattern yet.'**
  String get noProducts;

  /// No description provided for @viewProducts.
  ///
  /// In en, this message translates to:
  /// **'View products'**
  String get viewProducts;

  /// No description provided for @expertVerified.
  ///
  /// In en, this message translates to:
  /// **'Expert verified'**
  String get expertVerified;

  /// No description provided for @notExpertVerified.
  ///
  /// In en, this message translates to:
  /// **'Not yet expert verified'**
  String get notExpertVerified;

  /// No description provided for @inCatalog.
  ///
  /// In en, this message translates to:
  /// **'In catalog'**
  String get inCatalog;

  /// No description provided for @notInCatalog.
  ///
  /// In en, this message translates to:
  /// **'Not in catalog'**
  String get notInCatalog;

  /// No description provided for @taxonomyVerified.
  ///
  /// In en, this message translates to:
  /// **'Name checked in GBIF'**
  String get taxonomyVerified;

  /// No description provided for @sources.
  ///
  /// In en, this message translates to:
  /// **'Sources'**
  String get sources;

  /// No description provided for @warnings.
  ///
  /// In en, this message translates to:
  /// **'Notes'**
  String get warnings;

  /// No description provided for @retry.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retry;

  /// No description provided for @backHome.
  ///
  /// In en, this message translates to:
  /// **'Back to home'**
  String get backHome;

  /// No description provided for @newPhoto.
  ///
  /// In en, this message translates to:
  /// **'New photo'**
  String get newPhoto;

  /// No description provided for @openPattern.
  ///
  /// In en, this message translates to:
  /// **'Open pattern'**
  String get openPattern;

  /// No description provided for @openOrganism.
  ///
  /// In en, this message translates to:
  /// **'Open organism'**
  String get openOrganism;

  /// No description provided for @organismsTab.
  ///
  /// In en, this message translates to:
  /// **'Organisms'**
  String get organismsTab;

  /// No description provided for @fliesTab.
  ///
  /// In en, this message translates to:
  /// **'Flies'**
  String get fliesTab;

  /// No description provided for @searchHint.
  ///
  /// In en, this message translates to:
  /// **'Search by name'**
  String get searchHint;

  /// No description provided for @filterAll.
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get filterAll;

  /// No description provided for @emptyCatalog.
  ///
  /// In en, this message translates to:
  /// **'The catalog is empty for now.'**
  String get emptyCatalog;

  /// No description provided for @emptySearch.
  ///
  /// In en, this message translates to:
  /// **'Nothing matches your search.'**
  String get emptySearch;

  /// No description provided for @noImages.
  ///
  /// In en, this message translates to:
  /// **'No licensed photos yet'**
  String get noImages;

  /// No description provided for @photoCredit.
  ///
  /// In en, this message translates to:
  /// **'Photo: {attribution} · {license}'**
  String photoCredit(String attribution, String license);

  /// No description provided for @taxonomy.
  ///
  /// In en, this message translates to:
  /// **'Taxonomy'**
  String get taxonomy;

  /// No description provided for @habitat.
  ///
  /// In en, this message translates to:
  /// **'Habitat'**
  String get habitat;

  /// No description provided for @lifeStages.
  ///
  /// In en, this message translates to:
  /// **'Life stages'**
  String get lifeStages;

  /// No description provided for @distribution.
  ///
  /// In en, this message translates to:
  /// **'Distribution'**
  String get distribution;

  /// No description provided for @description.
  ///
  /// In en, this message translates to:
  /// **'Description'**
  String get description;

  /// No description provided for @fishingNotes.
  ///
  /// In en, this message translates to:
  /// **'For anglers'**
  String get fishingNotes;

  /// No description provided for @materials.
  ///
  /// In en, this message translates to:
  /// **'Materials'**
  String get materials;

  /// No description provided for @hookSizes.
  ///
  /// In en, this message translates to:
  /// **'Hook sizes'**
  String get hookSizes;

  /// No description provided for @hookRange.
  ///
  /// In en, this message translates to:
  /// **'#{max} – #{min}'**
  String hookRange(String max, String min);

  /// No description provided for @imitatedBy.
  ///
  /// In en, this message translates to:
  /// **'Imitated by'**
  String get imitatedBy;

  /// No description provided for @dataReviewNote.
  ///
  /// In en, this message translates to:
  /// **'Catalog data pending expert review.'**
  String get dataReviewNote;

  /// No description provided for @gbifLink.
  ///
  /// In en, this message translates to:
  /// **'View on GBIF'**
  String get gbifLink;

  /// No description provided for @productsTitle.
  ///
  /// In en, this message translates to:
  /// **'Products'**
  String get productsTitle;

  /// No description provided for @priceNotAvailable.
  ///
  /// In en, this message translates to:
  /// **'Price not available'**
  String get priceNotAvailable;

  /// No description provided for @lastVerified.
  ///
  /// In en, this message translates to:
  /// **'Checked {date}'**
  String lastVerified(String date);

  /// No description provided for @shipsToYou.
  ///
  /// In en, this message translates to:
  /// **'Ships to your country'**
  String get shipsToYou;

  /// No description provided for @openStore.
  ///
  /// In en, this message translates to:
  /// **'Open store page'**
  String get openStore;

  /// No description provided for @cannotOpenLink.
  ///
  /// In en, this message translates to:
  /// **'Could not open the link.'**
  String get cannotOpenLink;

  /// No description provided for @historyEmpty.
  ///
  /// In en, this message translates to:
  /// **'Your identifications will appear here.'**
  String get historyEmpty;

  /// No description provided for @errorNetwork.
  ///
  /// In en, this message translates to:
  /// **'No connection to the server. Check your internet connection.'**
  String get errorNetwork;

  /// No description provided for @errorTimeout.
  ///
  /// In en, this message translates to:
  /// **'The server took too long to answer. Please try again.'**
  String get errorTimeout;

  /// No description provided for @errorServer.
  ///
  /// In en, this message translates to:
  /// **'The server could not complete the request.'**
  String get errorServer;

  /// No description provided for @errorRateLimited.
  ///
  /// In en, this message translates to:
  /// **'Too many attempts. Wait a minute and try again.'**
  String get errorRateLimited;

  /// No description provided for @errorInvalidImage.
  ///
  /// In en, this message translates to:
  /// **'The photo could not be read. Try another one.'**
  String get errorInvalidImage;

  /// No description provided for @errorTooLarge.
  ///
  /// In en, this message translates to:
  /// **'The photo is too large.'**
  String get errorTooLarge;

  /// No description provided for @errorUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Image analysis is temporarily unavailable. Please try again later.'**
  String get errorUnavailable;

  /// No description provided for @errorNotFound.
  ///
  /// In en, this message translates to:
  /// **'Not found.'**
  String get errorNotFound;

  /// No description provided for @errorUnknown.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong.'**
  String get errorUnknown;

  /// No description provided for @matchLevel_high_match.
  ///
  /// In en, this message translates to:
  /// **'High match'**
  String get matchLevel_high_match;

  /// No description provided for @matchLevel_moderate_match.
  ///
  /// In en, this message translates to:
  /// **'Moderate match'**
  String get matchLevel_moderate_match;

  /// No description provided for @matchLevel_low_match.
  ///
  /// In en, this message translates to:
  /// **'Low match'**
  String get matchLevel_low_match;

  /// No description provided for @matchLevel_inconclusive.
  ///
  /// In en, this message translates to:
  /// **'Inconclusive'**
  String get matchLevel_inconclusive;

  /// No description provided for @matchLevel_insufficient_image.
  ///
  /// In en, this message translates to:
  /// **'Photo not good enough'**
  String get matchLevel_insufficient_image;

  /// No description provided for @matchLevel_not_compatible.
  ///
  /// In en, this message translates to:
  /// **'Not suitable for this function'**
  String get matchLevel_not_compatible;

  /// No description provided for @aiConfidence.
  ///
  /// In en, this message translates to:
  /// **'AI confidence: {level}'**
  String aiConfidence(String level);

  /// No description provided for @confidence_high.
  ///
  /// In en, this message translates to:
  /// **'high'**
  String get confidence_high;

  /// No description provided for @confidence_moderate.
  ///
  /// In en, this message translates to:
  /// **'moderate'**
  String get confidence_moderate;

  /// No description provided for @confidence_low.
  ///
  /// In en, this message translates to:
  /// **'low'**
  String get confidence_low;

  /// No description provided for @confidence_none.
  ///
  /// In en, this message translates to:
  /// **'none'**
  String get confidence_none;

  /// No description provided for @lifeStage_egg.
  ///
  /// In en, this message translates to:
  /// **'Egg'**
  String get lifeStage_egg;

  /// No description provided for @lifeStage_larva.
  ///
  /// In en, this message translates to:
  /// **'Larva'**
  String get lifeStage_larva;

  /// No description provided for @lifeStage_nymph.
  ///
  /// In en, this message translates to:
  /// **'Nymph'**
  String get lifeStage_nymph;

  /// No description provided for @lifeStage_pupa.
  ///
  /// In en, this message translates to:
  /// **'Pupa'**
  String get lifeStage_pupa;

  /// No description provided for @lifeStage_emerger.
  ///
  /// In en, this message translates to:
  /// **'Emerger'**
  String get lifeStage_emerger;

  /// No description provided for @lifeStage_subimago.
  ///
  /// In en, this message translates to:
  /// **'Dun (subimago)'**
  String get lifeStage_subimago;

  /// No description provided for @lifeStage_imago.
  ///
  /// In en, this message translates to:
  /// **'Spinner (imago)'**
  String get lifeStage_imago;

  /// No description provided for @lifeStage_adult.
  ///
  /// In en, this message translates to:
  /// **'Adult'**
  String get lifeStage_adult;

  /// No description provided for @lifeStage_juvenile.
  ///
  /// In en, this message translates to:
  /// **'Juvenile'**
  String get lifeStage_juvenile;

  /// No description provided for @lifeStage_other.
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get lifeStage_other;

  /// No description provided for @lifeStage_unknown.
  ///
  /// In en, this message translates to:
  /// **'Unknown'**
  String get lifeStage_unknown;

  /// No description provided for @category_dry_fly.
  ///
  /// In en, this message translates to:
  /// **'Dry fly'**
  String get category_dry_fly;

  /// No description provided for @category_nymph.
  ///
  /// In en, this message translates to:
  /// **'Nymph'**
  String get category_nymph;

  /// No description provided for @category_emerger.
  ///
  /// In en, this message translates to:
  /// **'Emerger'**
  String get category_emerger;

  /// No description provided for @category_wet_fly.
  ///
  /// In en, this message translates to:
  /// **'Wet fly'**
  String get category_wet_fly;

  /// No description provided for @category_streamer.
  ///
  /// In en, this message translates to:
  /// **'Streamer'**
  String get category_streamer;

  /// No description provided for @category_terrestrial.
  ///
  /// In en, this message translates to:
  /// **'Terrestrial'**
  String get category_terrestrial;

  /// No description provided for @category_saltwater.
  ///
  /// In en, this message translates to:
  /// **'Saltwater'**
  String get category_saltwater;

  /// No description provided for @category_attractor.
  ///
  /// In en, this message translates to:
  /// **'Attractor'**
  String get category_attractor;

  /// No description provided for @category_other.
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get category_other;

  /// No description provided for @matchType_exact_imitation.
  ///
  /// In en, this message translates to:
  /// **'Exact imitation'**
  String get matchType_exact_imitation;

  /// No description provided for @matchType_general_imitation.
  ///
  /// In en, this message translates to:
  /// **'General imitation'**
  String get matchType_general_imitation;

  /// No description provided for @matchType_suggestive_imitation.
  ///
  /// In en, this message translates to:
  /// **'Suggestive imitation'**
  String get matchType_suggestive_imitation;

  /// No description provided for @matchType_attractor.
  ///
  /// In en, this message translates to:
  /// **'Attractor'**
  String get matchType_attractor;

  /// No description provided for @matchType_not_specified.
  ///
  /// In en, this message translates to:
  /// **'Not specified'**
  String get matchType_not_specified;

  /// No description provided for @compat_high.
  ///
  /// In en, this message translates to:
  /// **'High biological compatibility'**
  String get compat_high;

  /// No description provided for @compat_medium.
  ///
  /// In en, this message translates to:
  /// **'Medium biological compatibility'**
  String get compat_medium;

  /// No description provided for @compat_low.
  ///
  /// In en, this message translates to:
  /// **'Low biological compatibility'**
  String get compat_low;

  /// No description provided for @compat_unknown.
  ///
  /// In en, this message translates to:
  /// **'Unknown biological compatibility'**
  String get compat_unknown;

  /// No description provided for @tier_biological_same_stage.
  ///
  /// In en, this message translates to:
  /// **'Documented for this life stage'**
  String get tier_biological_same_stage;

  /// No description provided for @tier_biological_stage_unknown.
  ///
  /// In en, this message translates to:
  /// **'Documented (stage not determined)'**
  String get tier_biological_stage_unknown;

  /// No description provided for @tier_biological_other_stage.
  ///
  /// In en, this message translates to:
  /// **'Documented for another life stage'**
  String get tier_biological_other_stage;

  /// No description provided for @tier_visual_only.
  ///
  /// In en, this message translates to:
  /// **'Only visually similar'**
  String get tier_visual_only;

  /// No description provided for @group_aquatic_insect.
  ///
  /// In en, this message translates to:
  /// **'Aquatic insects'**
  String get group_aquatic_insect;

  /// No description provided for @group_terrestrial_insect.
  ///
  /// In en, this message translates to:
  /// **'Terrestrial insects'**
  String get group_terrestrial_insect;

  /// No description provided for @group_crustacean.
  ///
  /// In en, this message translates to:
  /// **'Crustaceans'**
  String get group_crustacean;

  /// No description provided for @group_annelid.
  ///
  /// In en, this message translates to:
  /// **'Worms and leeches'**
  String get group_annelid;

  /// No description provided for @group_mollusc.
  ///
  /// In en, this message translates to:
  /// **'Molluscs'**
  String get group_mollusc;

  /// No description provided for @group_fish.
  ///
  /// In en, this message translates to:
  /// **'Fish'**
  String get group_fish;

  /// No description provided for @group_other.
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get group_other;

  /// No description provided for @habitat_freshwater_running.
  ///
  /// In en, this message translates to:
  /// **'Running water'**
  String get habitat_freshwater_running;

  /// No description provided for @habitat_freshwater_still.
  ///
  /// In en, this message translates to:
  /// **'Still water'**
  String get habitat_freshwater_still;

  /// No description provided for @habitat_estuarine.
  ///
  /// In en, this message translates to:
  /// **'Estuaries'**
  String get habitat_estuarine;

  /// No description provided for @habitat_marine.
  ///
  /// In en, this message translates to:
  /// **'Sea'**
  String get habitat_marine;

  /// No description provided for @habitat_terrestrial.
  ///
  /// In en, this message translates to:
  /// **'Land'**
  String get habitat_terrestrial;

  /// No description provided for @availability_in_stock.
  ///
  /// In en, this message translates to:
  /// **'In stock'**
  String get availability_in_stock;

  /// No description provided for @availability_out_of_stock.
  ///
  /// In en, this message translates to:
  /// **'Out of stock'**
  String get availability_out_of_stock;

  /// No description provided for @availability_preorder.
  ///
  /// In en, this message translates to:
  /// **'Pre-order'**
  String get availability_preorder;

  /// No description provided for @availability_discontinued.
  ///
  /// In en, this message translates to:
  /// **'Discontinued'**
  String get availability_discontinued;

  /// No description provided for @availability_unknown.
  ///
  /// In en, this message translates to:
  /// **'Availability unknown'**
  String get availability_unknown;

  /// No description provided for @kind_organism.
  ///
  /// In en, this message translates to:
  /// **'Organism'**
  String get kind_organism;

  /// No description provided for @kind_fly.
  ///
  /// In en, this message translates to:
  /// **'Fly'**
  String get kind_fly;

  /// No description provided for @kingdom.
  ///
  /// In en, this message translates to:
  /// **'Kingdom'**
  String get kingdom;

  /// No description provided for @phylum.
  ///
  /// In en, this message translates to:
  /// **'Phylum'**
  String get phylum;

  /// No description provided for @className.
  ///
  /// In en, this message translates to:
  /// **'Class'**
  String get className;

  /// No description provided for @species.
  ///
  /// In en, this message translates to:
  /// **'Species'**
  String get species;

  /// No description provided for @rank_kingdom.
  ///
  /// In en, this message translates to:
  /// **'kingdom'**
  String get rank_kingdom;

  /// No description provided for @rank_phylum.
  ///
  /// In en, this message translates to:
  /// **'phylum'**
  String get rank_phylum;

  /// No description provided for @rank_class.
  ///
  /// In en, this message translates to:
  /// **'class'**
  String get rank_class;

  /// No description provided for @rank_subclass.
  ///
  /// In en, this message translates to:
  /// **'subclass'**
  String get rank_subclass;

  /// No description provided for @rank_order.
  ///
  /// In en, this message translates to:
  /// **'order'**
  String get rank_order;

  /// No description provided for @rank_suborder.
  ///
  /// In en, this message translates to:
  /// **'suborder'**
  String get rank_suborder;

  /// No description provided for @rank_infraorder.
  ///
  /// In en, this message translates to:
  /// **'infraorder'**
  String get rank_infraorder;

  /// No description provided for @rank_superfamily.
  ///
  /// In en, this message translates to:
  /// **'superfamily'**
  String get rank_superfamily;

  /// No description provided for @rank_family.
  ///
  /// In en, this message translates to:
  /// **'family'**
  String get rank_family;

  /// No description provided for @rank_subfamily.
  ///
  /// In en, this message translates to:
  /// **'subfamily'**
  String get rank_subfamily;

  /// No description provided for @rank_genus.
  ///
  /// In en, this message translates to:
  /// **'genus'**
  String get rank_genus;

  /// No description provided for @rank_species.
  ///
  /// In en, this message translates to:
  /// **'species'**
  String get rank_species;

  /// No description provided for @rank_subspecies.
  ///
  /// In en, this message translates to:
  /// **'subspecies'**
  String get rank_subspecies;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'es'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'es':
      return AppLocalizationsEs();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
