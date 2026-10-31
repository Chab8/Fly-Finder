"""Server-generated user-facing strings (warnings, recommendation reasons) in en/es.

Catalog content has its own per-language tables; this covers only text the backend writes.
"""

from __future__ import annotations

SUPPORTED_LANGUAGES = ("en", "es")

LIFE_STAGES = {
    "en": {
        "egg": "egg", "larva": "larva", "nymph": "nymph", "pupa": "pupa", "emerger": "emerger",
        "subimago": "dun (subimago)", "imago": "spinner (imago)", "adult": "adult", "juvenile": "juvenile",
        "other": "other stage", "unknown": "unknown stage",
    },
    "es": {
        "egg": "huevo", "larva": "larva", "nymph": "ninfa", "pupa": "pupa", "emerger": "emergente",
        "subimago": "subimago (dun)", "imago": "imago (spinner)", "adult": "adulto", "juvenile": "juvenil",
        "other": "otra etapa", "unknown": "etapa desconocida",
    },
}

MESSAGES: dict[str, dict[str, str]] = {
    # --- warnings -------------------------------------------------------------
    "low_resolution": {
        "en": "Low-resolution photo: fine details may not be visible.",
        "es": "Foto de baja resolución: pueden no verse los detalles finos.",
    },
    "possibly_blurry": {
        "en": "The photo looks out of focus. A sharper photo improves the result.",
        "es": "La foto parece desenfocada. Una foto más nítida mejora el resultado.",
    },
    "ai_unavailable": {
        "en": "AI analysis is unavailable right now. Results use visual similarity only and are not an identification.",
        "es": "El análisis con IA no está disponible ahora. Los resultados usan solo similitud visual y no son una identificación.",
    },
    "ai_bad_response": {
        "en": "The AI returned an invalid answer and it was discarded.",
        "es": "La IA devolvió una respuesta inválida y fue descartada.",
    },
    "embeddings_unavailable": {
        "en": "Visual similarity search is unavailable; results rely on AI analysis and catalog data.",
        "es": "La búsqueda por similitud visual no está disponible; los resultados se basan en la IA y el catálogo.",
    },
    "taxonomy_unavailable": {
        "en": "GBIF could not be reached, so names were not checked against the taxonomic backbone.",
        "es": "No se pudo consultar GBIF, así que los nombres no se verificaron contra la taxonomía de referencia.",
    },
    "taxonomy_not_matched": {
        "en": "The proposed name '{name}' was not found in GBIF. Treat it with caution.",
        "es": "El nombre propuesto '{name}' no se encontró en GBIF. Tomalo con precaución.",
    },
    "not_in_catalog": {
        "en": "'{name}' is not in our catalog yet. This suggestion has not been verified by our database.",
        "es": "'{name}' todavía no está en nuestro catálogo. Esta sugerencia no fue verificada por nuestra base de datos.",
    },
    "species_level_uncertain": {
        "en": "Species-level identification from a photo is often unreliable; family or genus is more dependable.",
        "es": "Identificar la especie con una foto suele ser poco confiable; la familia o el género son más seguros.",
    },
    "wrong_subject_organism": {
        "en": "This looks like an artificial fly. Use 'Identify a fly' instead.",
        "es": "Parece una mosca artificial. Usá 'Identificar mosca'.",
    },
    "wrong_subject_fly": {
        "en": "This looks like a real organism, not an artificial fly. Use 'Identify an organism' instead.",
        "es": "Parece un organismo real, no una mosca artificial. Usá 'Identificar organismo'.",
    },
    "no_subject": {
        "en": "No organism or fly could be recognised in this photo.",
        "es": "No se reconoció ningún organismo ni mosca en esta foto.",
    },
    "insufficient_image": {
        "en": "The photo is not good enough to analyse: {issues}.",
        "es": "La foto no alcanza para analizarla: {issues}.",
    },
    "inconclusive_identification": {
        "en": "The photo does not allow a reliable identification.",
        "es": "La foto no permite una identificación confiable.",
    },
    "no_recommendations": {
        "en": "No documented fly patterns for this organism in our catalog yet.",
        "es": "Todavía no hay moscas documentadas para este organismo en nuestro catálogo.",
    },
    "relations_unverified": {
        "en": "Some recommendations come from relations not yet verified by an expert.",
        "es": "Algunas recomendaciones provienen de relaciones aún no verificadas por un experto.",
    },
    "attractor_pattern": {
        "en": "This pattern is an attractor: it does not imitate a specific organism.",
        "es": "Este patrón es un atractor: no imita un organismo específico.",
    },
    "fuzzy_pattern_name": {
        "en": "The pattern name was matched approximately to '{name}'.",
        "es": "El nombre del patrón se asoció de forma aproximada a '{name}'.",
    },
    "demo_mode": {
        "en": "DEMO MODE: fictional data. No real identification was performed.",
        "es": "MODO DEMO: datos ficticios. No se realizó ninguna identificación real.",
    },
    "image_storage_skipped": {
        "en": "Your photo was not stored.",
        "es": "Tu foto no se guardó.",
    },
    # --- recommendation reasons ----------------------------------------------
    "reason_relation": {
        "en": "Documented imitation of {organism} ({stage}).",
        "es": "Imitación documentada de {organism} ({stage}).",
    },
    "reason_broader_group": {
        "en": "Recommended for the broader group {organism}.",
        "es": "Recomendada para el grupo más amplio {organism}.",
    },
    "reason_related_taxon": {
        "en": "No fly is documented for this taxon; documented for {organism}, a relative in the same order ({order}).",
        "es": "No hay moscas documentadas para este taxón; documentada para {organism}, un pariente del mismo orden ({order}).",
    },
    "reason_expert_verified": {
        "en": "Relation verified by an expert ({source}).",
        "es": "Relación verificada por un experto ({source}).",
    },
    "reason_unverified": {
        "en": "Relation not yet verified by an expert.",
        "es": "Relación aún no verificada por un experto.",
    },
    "reason_same_stage": {
        "en": "Matches the observed life stage.",
        "es": "Coincide con la etapa de vida observada.",
    },
    "reason_other_stage": {
        "en": "Imitates the {stage}, while the photo shows the {observed}.",
        "es": "Imita la etapa {stage}, mientras que la foto muestra {observed}.",
    },
    "reason_colors": {
        "en": "Shares colours: {colors}.",
        "es": "Comparte colores: {colors}.",
    },
    "reason_visual": {
        "en": "Looks similar to catalog photos (visual similarity {similarity}, not a probability).",
        "es": "Se parece a fotos del catálogo (similitud visual {similarity}, no es una probabilidad).",
    },
    "reason_visual_only": {
        "en": "Only visual similarity: no documented biological relationship.",
        "es": "Solo similitud visual: no hay relación biológica documentada.",
    },
}


# Colour words the vision model returns (always English) -> display names. Unknown words are kept.
COLORS_ES = {
    "olive": "oliva", "olive green": "verde oliva", "green": "verde", "chartreuse": "chartreuse", "brown": "marrón",
    "dark brown": "marrón oscuro", "light brown": "marrón claro", "rust": "óxido", "rusty": "óxido", "mahogany": "caoba",
    "tan": "canela", "cream": "crema", "beige": "beige", "sand": "arena", "sulphur": "azufre", "yellow": "amarillo",
    "pale yellow": "amarillo pálido", "golden": "dorado", "gold": "dorado", "amber": "ámbar", "orange": "naranja",
    "grey": "gris", "gray": "gris", "dark grey": "gris oscuro", "dark gray": "gris oscuro", "light grey": "gris claro",
    "light gray": "gris claro", "dun": "dun (gris pardo)", "blue dun": "gris azulado", "grizzly": "grizzly (barrado)",
    "black": "negro", "white": "blanco", "silver": "plateado", "red": "rojo", "pink": "rosa", "purple": "violeta",
    "blue": "azul", "translucent": "translúcido", "clear": "transparente", "copper": "cobre", "bronze": "bronce",
    "pearl": "perlado", "iridescent": "iridiscente", "mottled": "moteado", "speckled": "moteado", "barred": "barrado",
}


def color_name(color: str, lang: str) -> str:
    if lang != "es":
        return color
    return COLORS_ES.get(color.strip().lower(), color)


def normalize_language(lang: str | None) -> str:
    code = (lang or "en").split(",")[0].split("-")[0].strip().lower()
    return code if code in SUPPORTED_LANGUAGES else "en"


def t(code: str, lang: str, **params: object) -> str:
    templates = MESSAGES[code]
    return templates.get(lang, templates["en"]).format(**params)


def stage_name(stage: str, lang: str) -> str:
    return LIFE_STAGES.get(lang, LIFE_STAGES["en"]).get(stage, stage)
