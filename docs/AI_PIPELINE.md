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

`services/recommendations/ranking.py`, versión `heuristic-v0.1`.

**Niveles (nunca se mezclan, en este orden):**
1. Relación documentada para la etapa observada.
2. Relación documentada, etapa no determinada.
3. Relación documentada para otra etapa.
4. Solo similitud visual (≥0,25), sin relación biológica. Siempre al final.

**Dentro de cada nivel**, promedio ponderado de los componentes disponibles (los ausentes no penalizan):

| Componente | Peso inicial | Valores |
|---|---|---|
| Compatibilidad biológica | 0,40 | high 1 · medium 0,6 · low 0,3 · unknown 0,15 |
| Etapa de vida | 0,25 | misma 1 · relacionada (dun/spinner/adulto; pupa/emergente; ninfa/larva) 0,6 · desconocida 0,5 · distinta 0,1 |
| Especificidad taxonómica | 0,15 | 1 − 0,1 por cada nivel entre el taxón identificado y el de la relación (mín. 0,3) |
| Tipo de imitación | 0,10 | exacta 1 · general 0,75 · sugestiva 0,5 · sin especificar 0,4 · atractor 0,3 |
| Color | 0,05 | proporción de familias de color compartidas |
| Similitud visual | 0,05 | coseno reescalado de 0,15–0,60 a 0–1 |

> **Estos pesos son heurísticas experimentales**, no verdades científicas. Deben calibrarse con el set de evaluación ([TESTING.md](TESTING.md)). Se cambian en `RankingConfig` sin tocar el resto.

**Factores no usados todavía, y por qué:**
- *Tamaño*: los tamaños de anzuelo no están estandarizados entre fabricantes y el catálogo aún no tiene tamaños de organismos con fuente. Se muestran, no se puntúan.
- *Geografía*: el catálogo no tiene distribución con fuente por taxón. Preparado para agregarse como componente.

## Modelos

| Uso | Modelo | Licencia / notas |
|---|---|---|
| Visión | `gemini-3.8-flash` (variable `GEMINI_MODEL`) | Verificado en ai.google.dev el 2026-10-31 como modelo estable recomendado. Alternativa más barata: `gemini-3.5-flash-lite`. |
| Embeddings | OpenCLIP `ViT-B-32` + `laion2b_s34b_b79k` | Código MIT; pesos MIT (tarjeta de Hugging Face `laion/CLIP-ViT-B-32-laion2B-s34B-b79K`). 512 dimensiones = columnas `vector(512)`. Liviano para CPU. |

Cambiar el modelo de embeddings requiere: nueva fila en `model_versions`, migración si cambia la dimensión, y correr `scripts/generate_embeddings.py`. Los vectores de modelos distintos nunca se comparan (la búsqueda filtra por `embedding_model`).

## Modo DEMO

`DEMO_MODE=true` usa `DemoVisionAnalyzer`: respuestas fijas que nombran registros ficticios (`Demoensis ficticius`, "DEMO Nymph"), sin ningún análisis. Toda respuesta lleva `analysis.is_demo=true`, la advertencia `demo_mode` y la app muestra una franja "MODO DEMO". Una foto muy oscura devuelve `insufficient_image` para probar ese flujo. El modo DEMO está prohibido en producción (la configuración no arranca).

## Limitaciones conocidas

- Identificar especies por foto es poco confiable para la mayoría de los insectos acuáticos; el sistema lo advierte y prefiere familia o género.
- Gemini escribe los textos libres (rasgos, evidencia) en inglés; los colores se comparan con un mapa de familias de color en inglés.
- El catálogo aún no tiene fotos con licencia, así que la búsqueda visual devuelve vacío hasta cargarlas y generar embeddings.
- Ninguna relación organismo↔mosca está verificada por un experto todavía (todas `expert_verified=false`).
- La similitud de OpenCLIP entre una foto de insecto y una foto de mosca artificial es una señal débil; por eso pesa 5 %.
