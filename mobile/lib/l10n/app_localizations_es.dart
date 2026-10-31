// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Spanish Castilian (`es`).
class AppLocalizationsEs extends AppLocalizations {
  AppLocalizationsEs([String locale = 'es']) : super(locale);

  @override
  String get homeTagline => 'Lo que eclosiona en el río, en tu caja de moscas.';

  @override
  String get identifyOrganismTitle => 'Identificar organismo';

  @override
  String get identifyOrganismSubtitle =>
      'Fotografiá un insecto, crustáceo o pez forraje y encontrá moscas que lo imiten.';

  @override
  String get identifyFlyTitle => 'Identificar mosca';

  @override
  String get identifyFlySubtitle =>
      'Fotografiá una mosca artificial y descubrí qué imita.';

  @override
  String get catalogTitle => 'Catálogo';

  @override
  String get catalogSubtitle => 'Organismos y patrones de moscas';

  @override
  String get historyTitle => 'Historial';

  @override
  String get historySubtitle => 'Tus identificaciones recientes';

  @override
  String get demoBanner =>
      'MODO DEMO · datos ficticios, sin identificación real';

  @override
  String get captureHintOrganism =>
      'Que el organismo ocupe la foto, enfocado y con buena luz. Una vista lateral ayuda.';

  @override
  String get captureHintFly =>
      'Apoyá la mosca sobre un fondo liso y fotografiala de costado.';

  @override
  String get takePhoto => 'Sacar foto';

  @override
  String get chooseFromGallery => 'Elegir de la galería';

  @override
  String get changePhoto => 'Cambiar foto';

  @override
  String get cancel => 'Cancelar';

  @override
  String get analyze => 'Analizar foto';

  @override
  String get noPhotoSelected => 'Todavía no elegiste una foto';

  @override
  String get permissionDenied =>
      'Se denegó el permiso para usar la cámara o las fotos. Podés habilitarlo en Ajustes.';

  @override
  String imageTooLargeLocal(int limit) {
    return 'La foto supera los $limit MB. Elegí una más liviana.';
  }

  @override
  String get unsupportedFormatLocal =>
      'Tipo de archivo no soportado. Usá JPEG, PNG, WEBP o HEIC.';

  @override
  String get phaseUploading => 'Enviando la foto';

  @override
  String get phaseAnalyzing => 'Analizando en el servidor';

  @override
  String get analysisNote => 'El análisis con IA puede tardar hasta un minuto.';

  @override
  String get resultOrganismTitle => 'Resultado del organismo';

  @override
  String get resultFlyTitle => 'Resultado de la mosca';

  @override
  String get primaryIdentification => 'Más probable';

  @override
  String get alternatives => 'Alternativas';

  @override
  String get noIdentification => 'Sin identificación';

  @override
  String get scientificName => 'Nombre científico';

  @override
  String get commonName => 'Nombre común';

  @override
  String get order => 'Orden';

  @override
  String get family => 'Familia';

  @override
  String get genus => 'Género';

  @override
  String get rank => 'Rango';

  @override
  String get lifeStage => 'Etapa de vida';

  @override
  String get characteristics => 'Características visibles';

  @override
  String get colors => 'Colores';

  @override
  String estimatedLength(String mm, String reference) {
    return 'Largo estimado: $mm mm ($reference)';
  }

  @override
  String get certainty => 'Nivel de certeza';

  @override
  String get certaintyExplanation =>
      'La certeza es un nivel cualitativo basado en reglas documentadas, no un porcentaje.';

  @override
  String get recommendedFlies => 'Moscas recomendadas';

  @override
  String get noRecommendations =>
      'Nuestro catálogo todavía no documenta moscas para este organismo.';

  @override
  String visualSimilarity(String value) {
    return 'Similitud visual $value';
  }

  @override
  String get notAProbability =>
      'La similitud y el puntaje de orden no son probabilidades.';

  @override
  String get similarOrganisms => 'Visualmente similares en el catálogo';

  @override
  String get imitates => 'Imita a';

  @override
  String get imitatesNothingDocumented =>
      'No hay organismos documentados para este patrón. Puede ser un atractor o un patrón general.';

  @override
  String get aiSuggestions => 'Sugerencias de la IA (sin verificar)';

  @override
  String get variants => 'Variantes';

  @override
  String get products => 'Dónde comprar';

  @override
  String get noProducts =>
      'Todavía no hay productos verificados para este patrón.';

  @override
  String get viewProducts => 'Ver productos';

  @override
  String get expertVerified => 'Verificado por experto';

  @override
  String get notExpertVerified => 'Aún sin verificar por experto';

  @override
  String get inCatalog => 'En el catálogo';

  @override
  String get notInCatalog => 'Fuera del catálogo';

  @override
  String get taxonomyVerified => 'Nombre verificado en GBIF';

  @override
  String get sources => 'Fuentes';

  @override
  String get warnings => 'Notas';

  @override
  String get retry => 'Reintentar';

  @override
  String get backHome => 'Volver al inicio';

  @override
  String get newPhoto => 'Nueva foto';

  @override
  String get openPattern => 'Ver patrón';

  @override
  String get openOrganism => 'Ver organismo';

  @override
  String get organismsTab => 'Organismos';

  @override
  String get fliesTab => 'Moscas';

  @override
  String get searchHint => 'Buscar por nombre';

  @override
  String get filterAll => 'Todos';

  @override
  String get emptyCatalog => 'Por ahora el catálogo está vacío.';

  @override
  String get emptySearch => 'No hay resultados para tu búsqueda.';

  @override
  String get noImages => 'Todavía sin fotos con licencia';

  @override
  String photoCredit(String attribution, String license) {
    return 'Foto: $attribution · $license';
  }

  @override
  String get taxonomy => 'Taxonomía';

  @override
  String get habitat => 'Hábitat';

  @override
  String get lifeStages => 'Etapas de vida';

  @override
  String get distribution => 'Distribución';

  @override
  String get description => 'Descripción';

  @override
  String get fishingNotes => 'Para el pescador';

  @override
  String get materials => 'Materiales';

  @override
  String get hookSizes => 'Tamaños de anzuelo';

  @override
  String hookRange(String max, String min) {
    return '#$max – #$min';
  }

  @override
  String get imitatedBy => 'Imitado por';

  @override
  String get dataReviewNote =>
      'Datos del catálogo pendientes de revisión experta.';

  @override
  String get gbifLink => 'Ver en GBIF';

  @override
  String get productsTitle => 'Productos';

  @override
  String get priceNotAvailable => 'Precio no disponible';

  @override
  String lastVerified(String date) {
    return 'Verificado el $date';
  }

  @override
  String get shipsToYou => 'Envía a tu país';

  @override
  String get openStore => 'Abrir página de la tienda';

  @override
  String get cannotOpenLink => 'No se pudo abrir el enlace.';

  @override
  String get historyEmpty => 'Tus identificaciones van a aparecer acá.';

  @override
  String get errorNetwork =>
      'Sin conexión con el servidor. Revisá tu conexión a internet.';

  @override
  String get errorTimeout =>
      'El servidor tardó demasiado en responder. Probá de nuevo.';

  @override
  String get errorServer => 'El servidor no pudo completar la solicitud.';

  @override
  String get errorRateLimited =>
      'Demasiados intentos. Esperá un minuto y probá de nuevo.';

  @override
  String get errorInvalidImage => 'No se pudo leer la foto. Probá con otra.';

  @override
  String get errorTooLarge => 'La foto es demasiado grande.';

  @override
  String get errorUnavailable =>
      'El análisis de imágenes no está disponible en este momento. Probá más tarde.';

  @override
  String get errorNotFound => 'No encontrado.';

  @override
  String get errorUnknown => 'Algo salió mal.';

  @override
  String get matchLevel_high_match => 'Coincidencia alta';

  @override
  String get matchLevel_moderate_match => 'Coincidencia moderada';

  @override
  String get matchLevel_low_match => 'Coincidencia baja';

  @override
  String get matchLevel_inconclusive => 'No concluyente';

  @override
  String get matchLevel_insufficient_image => 'Foto insuficiente';

  @override
  String get matchLevel_not_compatible => 'No corresponde a esta función';

  @override
  String aiConfidence(String level) {
    return 'Confianza de la IA: $level';
  }

  @override
  String get confidence_high => 'alta';

  @override
  String get confidence_moderate => 'moderada';

  @override
  String get confidence_low => 'baja';

  @override
  String get confidence_none => 'ninguna';

  @override
  String get lifeStage_egg => 'Huevo';

  @override
  String get lifeStage_larva => 'Larva';

  @override
  String get lifeStage_nymph => 'Ninfa';

  @override
  String get lifeStage_pupa => 'Pupa';

  @override
  String get lifeStage_emerger => 'Emergente';

  @override
  String get lifeStage_subimago => 'Dun (subimago)';

  @override
  String get lifeStage_imago => 'Spinner (imago)';

  @override
  String get lifeStage_adult => 'Adulto';

  @override
  String get lifeStage_juvenile => 'Juvenil';

  @override
  String get lifeStage_other => 'Otra';

  @override
  String get lifeStage_unknown => 'Desconocida';

  @override
  String get category_dry_fly => 'Seca';

  @override
  String get category_nymph => 'Ninfa';

  @override
  String get category_emerger => 'Emergente';

  @override
  String get category_wet_fly => 'Ahogada';

  @override
  String get category_streamer => 'Streamer';

  @override
  String get category_terrestrial => 'Terrestre';

  @override
  String get category_saltwater => 'Agua salada';

  @override
  String get category_attractor => 'Atractor';

  @override
  String get category_other => 'Otra';

  @override
  String get matchType_exact_imitation => 'Imitación exacta';

  @override
  String get matchType_general_imitation => 'Imitación general';

  @override
  String get matchType_suggestive_imitation => 'Imitación sugestiva';

  @override
  String get matchType_attractor => 'Atractor';

  @override
  String get matchType_not_specified => 'Sin especificar';

  @override
  String get compat_high => 'Compatibilidad biológica alta';

  @override
  String get compat_medium => 'Compatibilidad biológica media';

  @override
  String get compat_low => 'Compatibilidad biológica baja';

  @override
  String get compat_unknown => 'Compatibilidad biológica desconocida';

  @override
  String get tier_biological_same_stage => 'Documentada para esta etapa';

  @override
  String get tier_biological_stage_unknown =>
      'Documentada (etapa no determinada)';

  @override
  String get tier_biological_other_stage => 'Documentada para otra etapa';

  @override
  String get tier_visual_only => 'Solo similar visualmente';

  @override
  String get group_aquatic_insect => 'Insectos acuáticos';

  @override
  String get group_terrestrial_insect => 'Insectos terrestres';

  @override
  String get group_crustacean => 'Crustáceos';

  @override
  String get group_annelid => 'Gusanos y sanguijuelas';

  @override
  String get group_mollusc => 'Moluscos';

  @override
  String get group_fish => 'Peces';

  @override
  String get group_other => 'Otros';

  @override
  String get habitat_freshwater_running => 'Agua corriente';

  @override
  String get habitat_freshwater_still => 'Agua quieta';

  @override
  String get habitat_estuarine => 'Estuarios';

  @override
  String get habitat_marine => 'Mar';

  @override
  String get habitat_terrestrial => 'Tierra';

  @override
  String get availability_in_stock => 'En stock';

  @override
  String get availability_out_of_stock => 'Sin stock';

  @override
  String get availability_preorder => 'Preventa';

  @override
  String get availability_discontinued => 'Discontinuado';

  @override
  String get availability_unknown => 'Disponibilidad desconocida';

  @override
  String get kind_organism => 'Organismo';

  @override
  String get kind_fly => 'Mosca';

  @override
  String get kingdom => 'Reino';

  @override
  String get phylum => 'Filo';

  @override
  String get className => 'Clase';

  @override
  String get species => 'Especie';

  @override
  String get rank_kingdom => 'reino';

  @override
  String get rank_phylum => 'filo';

  @override
  String get rank_class => 'clase';

  @override
  String get rank_subclass => 'subclase';

  @override
  String get rank_order => 'orden';

  @override
  String get rank_suborder => 'suborden';

  @override
  String get rank_infraorder => 'infraorden';

  @override
  String get rank_superfamily => 'superfamilia';

  @override
  String get rank_family => 'familia';

  @override
  String get rank_subfamily => 'subfamilia';

  @override
  String get rank_genus => 'género';

  @override
  String get rank_species => 'especie';

  @override
  String get rank_subspecies => 'subespecie';
}
