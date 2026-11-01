# Motores de identificación

Dos servicios independientes: `OrganismIdentificationService` (Función A) y `FlyIdentificationService` (Función B), en `backend/app/services/identification/`. Comparten la base `IdentificationPipeline` (preparar imagen, llamar a la IA con protección, embeddings, registro).

## Tres señales que nunca se mezclan

| Señal | Origen | Qué significa | Qué NO significa |
|---|---|---|---|
| `ai_confidence` (high/moderate/low/none) | Autoevaluación de Gemini | Qué tan seguro dice estar el modelo | No es una probabilidad calibrada |
| `visual_similarity` (−1…1) | Coseno entre embeddings OpenCLIP | Cuánto se parecen dos imágenes para el modelo | No es probabilidad de identificación correcta ni compatibilidad biológica |
| `biological_compatibility` (high/medium/low/unknown) | Relaciones curadas en `fly_organism_matches` | Qué tan apropiada es la mosca para ese organismo y etapa | No depende de la foto |

## Función A — organismo real

1. Validar y normalizar imagen.
2. Gemini → `OrganismVisionResult` (tipo de sujeto, calidad, ≤5 candidatos al rango más específico justificable, etapa de vida, colores, rasgos; tamaño solo si hay referencia de escala).
3. Embedding OpenCLIP → organismos y moscas visualmente cercanos.
4. GBIF valida cada candidato (`/species/match`). Solo `matchType=EXACT` cuenta como verificado. Ejemplo real que motivó la regla: "Hirudinea" (sanguijuelas) da un `FUZZY` hacia *Hirundinea*, un género de aves.
5. Se busca el candidato principal y sus ancestros en el catálogo (especie → género → familia → orden → clase).
6. Ranking de moscas (abajo).
7. Respuesta con identificación principal, alternativas, etapa, rasgos, recomendaciones con justificación, organismos visualmente similares, fuentes y advertencias.

## Función B — mosca artificial

1. Validar imagen. 2. Gemini → `FlyVisionResult` (rasgos, categoría, ≤5 patrones, si parece atractor, grupos que podría imitar). Se le pasan los nombres del catálogo como referencia, sin obligarlo a elegir uno.
3. Cada nombre propuesto se busca en el catálogo: exacto → nombre alternativo → aproximado (≥0,86). Si no existe, se muestra igual, marcado "fuera del catálogo".
4. La búsqueda vectorial agrega candidatos solo visuales.
5. Para el patrón principal del catálogo: organismos que imita (relaciones curadas), variantes y productos.
6. Los atractores (Royal Wulff, Humpy…) no tienen relaciones biológicas forzadas; la app lo explica.

## Niveles de certeza (`match_level`)

Reglas en `services/identification/confidence.py`. No hay porcentajes.

| Situación | Nivel |
|---|---|
| Gemini dice calidad `unusable` | `insufficient_image` |
| Sujeto de la otra función (mosca en A, organismo en B) u objeto ajeno | `not_compatible` |
| Sin sujeto claro, o sin candidatos, o confianza `none` | `inconclusive` |
| Confianza de la IA high / moderate / low | `high_match` / `moderate_match` / `low_match`, bajando **un nivel** por cada condición: nombre no confirmado por GBIF (A), patrón fuera del catálogo (B), nombre asociado aproximadamente (B), foto `poor` |
| Gemini caído: solo similitud visual | como máximo `low_match` (si similitud ≥ 0,85); si no, `inconclusive` |
| Gemini y embeddings caídos | HTTP 503 `analysis_unavailable` |

## Ranking de moscas (Función A)

`services/recommendations/ranking.py`, versión `heuristic-v0.2` (v0.2, 2026-10-31: umbrales visuales recalibrados con el set de evaluación).

**Niveles (nunca se mezclan, en este orden):**
1. Relación documentada para la etapa observada.
2. Relación documentada, etapa no determinada.
3. Relación documentada para otra etapa.
4. Pariente del mismo orden: **solo** si ni el taxón identificado ni sus ancestros tienen relaciones en el catálogo, se usan las de los organismos del catálogo del mismo orden (p. ej. una ninfa identificada solo como "Anisoptera" recibe las moscas de Aeshnidae y Coenagrionidae). Especificidad fija en el mínimo (0,3) y el motivo lo dice.
5. Solo similitud visual (≥0,70), sin relación biológica. Siempre al final. Con 0,25 aparecían moscas sin relación: una foto de cangrejo de río da 0,63 contra una Adams seca.

**Dentro de cada nivel**, promedio ponderado de los componentes disponibles (los ausentes no penalizan):

| Componente | Peso inicial | Valores |
|---|---|---|
| Compatibilidad biológica | 0,40 | high 1 · medium 0,6 · low 0,3 · unknown 0,15 |
| Etapa de vida | 0,25 | misma 1 · relacionada (dun/spinner/adulto; pupa/emergente; ninfa/larva) 0,6 · desconocida 0,5 · distinta 0,1 |
| Especificidad taxonómica | 0,15 | 1 − 0,1 por cada nivel entre el taxón identificado y el de la relación (mín. 0,3) |
| Tipo de imitación | 0,10 | exacta 1 · general 0,75 · sugestiva 0,5 · sin especificar 0,4 · atractor 0,3 |
| Color | 0,05 | proporción de familias de color compartidas |
| Similitud visual | 0,05 | coseno reescalado de 0,50–0,80 a 0–1 (por debajo de 0,50 vale 0: foto de organismo contra foto de mosca da 0,50–0,63 aunque no se parezcan) |

> **Estos pesos son heurísticas experimentales**, no verdades científicas. Deben calibrarse con el set de evaluación ([TESTING.md](TESTING.md)). Se cambian en `RankingConfig` sin tocar el resto.

**Factores no usados todavía, y por qué:**
- *Tamaño*: los tamaños de anzuelo no están estandarizados entre fabricantes y el catálogo aún no tiene tamaños de organismos con fuente. Se muestran, no se puntúan.
- *Geografía*: el catálogo no tiene distribución con fuente por taxón. Preparado para agregarse como componente.

## Modelos

| Uso | Modelo | Licencia / notas |
|---|---|---|
| Visión | `gemini-3.8-flash` (variable `GEMINI_MODEL`) | Verificado en ai.google.dev el 2026-10-31 como modelo estable recomendado. Alternativa más rápida y barata: `gemini-3.5-flash-lite`. Razonamiento con `GEMINI_THINKING_LEVEL` (por defecto `low`). |
| Embeddings | OpenCLIP `ViT-B-32` + `laion2b_s34b_b79k` | Código MIT; pesos MIT (tarjeta de Hugging Face `laion/CLIP-ViT-B-32-laion2B-s34B-b79K`). 512 dimensiones = columnas `vector(512)`. Liviano para CPU. |

### Medición con Gemini real (2026-10-31, set de evaluación de 22 fotos)

| | `gemini-3.8-flash` | `gemini-3.5-flash-lite` |
|---|---|---|
| Tiempo por foto | 23–112 s (mediana ~80 s); hasta 51 s para responder solo "ok" | 3–10 s |
| Familia correcta (9 primeras fotos de organismos) | 8/9 (llega a subfamilia o género cuando puede) | 2/9 (casi siempre se queda en el orden) |
| Orden correcto | 9/9 | 13/13 |
| Patrón de mosca top-1 / top-3 | sin medir (la corrida se cortó) | 5–6/7 / 7/7 |
| Moscas recomendadas correctas en el top 3 | — | 11/13 |
| Controles (mapache → no compatible; foto borrosa → insuficiente) | — | 2/2 |

Con `GEMINI_TIMEOUT_SECONDS=45`, Flash se corta seguido y la app cae a "solo similitud visual". La latencia de Flash fue alta incluso para un texto de una palabra, así que no depende de la foto ni del prompt; puede ser carga del servicio o del nivel gratuito. Flash-Lite varía entre corridas (la misma foto puede quedar en familia u orden) y a veces afirma con certeza alta un patrón equivocado (Muddler → Royal Wulff, Crazy Charlie → Balanced Leech). Repetir la medición con `scripts/evaluate.py` al cambiar de modelo o de nivel de cuenta.

Cambiar el modelo de embeddings requiere: nueva fila en `model_versions`, migración si cambia la dimensión, y correr `scripts/generate_embeddings.py`. Los vectores de modelos distintos nunca se comparan (la búsqueda filtra por `embedding_model`).

### Lista de taxones del catálogo en el prompt (2026-10-31)

`ORGANISM_PROMPT` ahora incluye los taxones del catálogo (`CatalogSnapshot.organism_names()`, formato "Baetidae (family)") y pide no quedarse en el orden cuando se ven rasgos de una familia. Es opcional para el modelo: si el organismo no está en la lista, debe proponer su taxón real. **Falta medir el efecto** con `scripts/evaluate.py` (línea base con Flash-Lite: familia 6/13, orden 13/13).

### Perfiles de patrones, reintento y timeout (2026-10-31)

- `FLY_PROMPT` ahora recibe una línea por patrón del catálogo (`CatalogSnapshot.fly_profiles()`: categoría, colores, materiales y descripción, todo tomado del catálogo) y pide decidir primero la categoría de la mosca y usar confianza "high" solo con al menos dos rasgos distintivos visibles. La calidad de las descripciones del catálogo determina la calidad de esta ayuda.
- `run_ai` reintenta una vez ante errores transitorios del proveedor (`ai_unavailable`) y respuestas inválidas. No reintenta timeouts ni límites de cuota.
- `GEMINI_TIMEOUT_SECONDS` por defecto pasó de 45 a 60 s; la app espera hasta 130 s.

## Modo DEMO

`DEMO_MODE=true` usa `DemoVisionAnalyzer`: respuestas fijas que nombran registros ficticios (`Demoensis ficticius`, "DEMO Nymph"), sin ningún análisis. Toda respuesta lleva `analysis.is_demo=true`, la advertencia `demo_mode` y la app muestra una franja "MODO DEMO". Una foto muy oscura devuelve `insufficient_image` para probar ese flujo. El modo DEMO está prohibido en producción (la configuración no arranca).

## Limitaciones conocidas

- Identificar especies por foto es poco confiable para la mayoría de los insectos acuáticos; el sistema lo advierte y prefiere familia o género.
- Gemini escribe los textos libres (rasgos, evidencia, materiales) en el idioma del usuario, pero los colores siempre en inglés: se comparan con un mapa de familias de color y se traducen al mostrarlos (`services/i18n.py`, `COLORS_ES`).
- Hay 89 fotos de organismos (37 taxones) y 21 de moscas (14 de 69 patrones), con embeddings en Supabase. La búsqueda visual solo puede sugerir lo que tiene fotos.
- OpenCLIP ViT-B-32 casi no distingue patrones de moscas entre sí: cualquier mosca atada da 0,83–0,93 contra cualquier foto del catálogo (en la evaluación, una Woolly Bugger dio 0,905 contra una Parachute Adams y 0,871 contra la Woolly Bugger). Por eso, sin IA, una mosca necesita ≥0,95 para pasar de `inconclusive` a `low_match`, y la similitud visual nunca sube el nivel de una identificación.
- Ninguna relación organismo↔mosca está verificada por un experto todavía (todas `expert_verified=false`).
- La similitud de OpenCLIP entre una foto de insecto y una foto de mosca artificial es una señal débil; por eso pesa 5 %.
