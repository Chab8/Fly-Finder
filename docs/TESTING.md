# Pruebas y evaluación

## Backend

```bash
cd /Users/manuchab/Fly-Finder/backend && .venv/bin/python -m pytest
```

Resultado al 2026-10-31: **136 tests OK** (incluye 7 de base de datos real) y 1 salteado por defecto (el del modelo OpenCLIP real, que también pasó al ejecutarlo con `RUN_ML_TESTS=1`). Ninguna prueba llama a Gemini, GBIF ni iNaturalist: se usan dobles (`tests/conftest.py`) y `httpx.MockTransport`.

| Archivo | Cubre |
|---|---|
| `test_image_processing.py` | JPEG/PNG/WEBP/HEIC, formato por contenido, vacíos, demasiado grandes/chicos, alfa, orientación EXIF, borrado de GPS/EXIF, advertencias de desenfoque |
| `test_gemini_adapter.py` | Esquema JSON sin `$ref`, request bien formado, nivel de razonamiento (`thinking_level`), idioma del texto libre, respuestas inválidas o vacías, "no sé", clasificación de timeouts/429/401/500 |
| `test_catalog_data.py` | El catálogo real, el demo y las plantillas cargan sin errores; validaciones (binomio, anzuelos, fuente de verificación, precios) |
| `test_snapshot.py` | Búsqueda por nombre (exacto/alternativo/aproximado), linaje taxonómico, filtros, idioma con fallback, solo imágenes aprobadas, refresco tolerante a fallas |
| `test_ranking.py` | Niveles biológicos antes que visuales, especificidad, umbral visual, puntajes acotados, colores, parientes del mismo orden solo cuando no hay relaciones |
| `test_confidence.py` | Reglas de niveles de certeza |
| `test_identification_services.py` | Ambos motores: caso feliz, fuera de catálogo, GBIF no confirma, GBIF caído, sujeto incorrecto, foto inutilizable, IA caída (respaldo visual), todo caído (503), atractores, modo DEMO |
| `test_api.py` | Endpoints, errores consistentes, `Accept-Language`, límite de tamaño, rate limit, historial privado por cliente, productos y monedas |
| `test_infrastructure.py` | Configuración de producción, URL de Supabase con o sin `/rest/v1`, redacción de logs, índice vectorial, clientes GBIF/iNaturalist (filtro por estadio, reintentos ante cortes y 429), política de licencias |
| `test_contract_fixtures.py` | Contrato API↔app: regenera `mobile/test/fixtures/*.json` y falla si la forma cambia |
| `db/test_postgres.py` | **PostgreSQL 18 + pgvector reales**: migraciones, importación idempotente (sin perder `storage_path`), restricciones, búsqueda vectorial, historial, RLS para `anon` |
| `test_openclip.py` | Modelo OpenCLIP real (`RUN_ML_TESTS=1`, descarga ~600 MB la primera vez) |

Los tests de base crean un clúster temporal con `initdb` en un puerto libre y lo borran al terminar. Requieren `brew install postgresql@18 pgvector` (ya instalados en esta Mac); si faltan, se saltean.

```bash
cd backend && RUN_ML_TESTS=1 .venv/bin/python -m pytest tests/test_openclip.py
```

Después de cambiar un esquema de respuesta:

```bash
cd backend && WRITE_FIXTURES=1 .venv/bin/python -m pytest tests/test_contract_fixtures.py
```

## Flutter

```bash
cd /Users/manuchab/Fly-Finder/mobile && flutter test
```

Resultado al 2026-10-31: **20 tests OK**. Cubren parseo de respuestas reales de la API, navegación, localización es/en, selección de foto, tipo no soportado, permiso denegado, etapas de carga, flujo completo hasta el resultado, API caída con reintento, sin conexión, resultado no compatible, resultado de mosca con productos, catálogo vacío, búsqueda y filtros, ficha sin productos, producto sin precio, historial y formato de moneda.

También se verificó a mano en el simulador iOS (iPhone 17 Pro):
- 2026-10-31, modo DEMO: inicio, catálogo, ficha de organismo, selección desde la galería, análisis y resultados.
- 2026-10-31, **Gemini y Supabase reales**: una larva de Hydropsychidae (identificada a familia, verificada en GBIF, recomendaciones Czech Nymph y Walt's Worm para la larva) y una Woolly Bugger (coincidencia alta, foto del catálogo, imita Cottidae y Salmonidae, sugerencia de la IA "leech"). Textos en español.

## Evaluación real del reconocimiento

Las pruebas automáticas verifican que el sistema funciona, no que acierte. Para medir calidad:

**Set semilla (2026-10-31):** 22 fotos en `data/evaluation/manifest.csv`: 13 organismos de iNaturalist (observaciones distintas de las del catálogo), 7 moscas de Wikimedia Commons que no se cargaron en el catálogo, un mapache (debe dar `not_compatible`) y una foto desenfocada a propósito (debe dar `insufficient_image`). Las fotos no se suben a git; si `data/evaluation/images/` está vacío, bajalas de nuevo desde `source_url`. Resultados en [AI_PIPELINE.md → Medición](AI_PIPELINE.md#medición-con-gemini-real-2026-10-31-set-de-evaluación-de-22-fotos) y el último reporte en `data/evaluation/report.json`.

Para ampliarlo:

1. Juntá fotos **que no estén en el catálogo** (si están, la búsqueda visual encuentra la misma imagen y el resultado es engañoso). Objetivo inicial: 10 fotos por grupo principal y 30–50 moscas de patrones del catálogo, más 10–20 fotos "trampa" (objetos ajenos, fotos borrosas, moscas en modo organismo).
2. Guardalas en `data/evaluation/images/` (ignorado por git; respetá licencias igual).
3. Completá `data/evaluation/manifest.csv`: una fila por foto con lo esperado (`expected_family`, `expected_genus`, `expected_pattern_slug`, `expected_fly_slugs` aceptables, o `expected_outcome=not_compatible`/`insufficient_image`/`inconclusive`).
4. Con el backend corriendo con Gemini real:

```bash
cd /Users/manuchab/Fly-Finder && backend/.venv/bin/python scripts/evaluate.py --api http://localhost:8000 --lang es --out data/evaluation/report.json
```

Reporta precisión por orden, familia, género y especie; precisión de patrones top-1 y top-3; tasa de acierto de las 3 primeras recomendaciones; abstenciones correctas (el sistema reconoce que no sabe); y abstenciones sobre fotos identificables. Cada línea de `details` trae el resultado principal, el top 3 de moscas, si la IA respondió y cuánto tardó. **Cada foto consume una llamada a Gemini.** El script espera solo cuando la API devuelve 429 (`Retry-After`); con un modelo lento usá `--timeout 200`.

Usá los resultados para calibrar los pesos de `RankingConfig` y los umbrales de similitud. Una coincidencia visual alta no es una identificación correcta: el reporte compara contra la etiqueta esperada, no contra la similitud.
