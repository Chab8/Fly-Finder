# Arquitectura

## Visión general

```
┌──────────────┐  HTTPS multipart / JSON   ┌──────────────────────────── FastAPI ─────────────────────────────┐
│ Flutter app  │ ────────────────────────▶ │ api/v1 (rutas finas)                                              │
│ (sin claves) │ ◀──────────────────────── │   └─ services/identification  (OrganismIdentificationService,     │
└──────────────┘                           │        FlyIdentificationService)                                  │
                                           │        ├─ images/processing   validar, normalizar, quitar EXIF    │
                                           │        ├─ ai/                 VisionAnalyzer → Gemini | Demo       │
                                           │        ├─ embeddings/         ImageEmbedder → OpenCLIP             │
                                           │        ├─ taxonomy/           GBIF (nombres), iNaturalist (tooling)│
                                           │        ├─ recommendations/    ranking configurable                 │
                                           │        └─ commerce/           productos y tiendas                  │
                                           │ repositories/                                                     │
                                           │   ├─ catalog_snapshot   catálogo indexado en memoria              │
                                           │   ├─ postgres           TODO el SQL (loader, writer, pgvector, log)│
                                           │   └─ vector_index / identification_store (interfaces + memoria)   │
                                           └───────────────┬───────────────────────────┬──────────────────────┘
                                                           │                           │
                                         Supabase Postgres + pgvector          Gemini API · GBIF API
                                         Supabase Storage (fotos catálogo)
```

## Principios

- **Los endpoints no contienen lógica**: validan entrada, llaman a un servicio y devuelven un esquema Pydantic.
- **Proveedores detrás de interfaces** (`VisionAnalyzer`, `ImageEmbedder`, `VectorIndex`, `IdentificationStore`). Gemini no se conoce fuera de `services/ai/gemini.py`; se puede cambiar de proveedor sin tocar los motores.
- **Todo el SQL vive en `repositories/postgres.py`**. No hay consultas improvisadas en el resto del código.
- **Tres señales separadas**: confianza de la IA (cualitativa), similitud visual (coseno) y compatibilidad biológica (relaciones curadas). Nunca se mezclan ni se presentan como probabilidad.
- **Fallas controladas**: si Gemini cae, se responde con similitud visual (marcada como no-identificación); si GBIF cae, se avisa; si todo cae, `503 analysis_unavailable`. Nunca un 500 por un proveedor externo.

## Decisión técnica: catálogo en memoria + pgvector

El catálogo curado (cientos a decenas de miles de registros) se carga en un `CatalogSnapshot` indexado en memoria y se refresca cada `CATALOG_REFRESH_SECONDS` (300 s). Ventajas: búsquedas y armado de fichas sin N consultas por request, una sola implementación de consultas para los modos `memory` y `postgres`, y todo el SQL en un único módulo. Si un refresco falla, se sigue sirviendo el snapshot anterior.

Lo que **no** pasa por memoria: la búsqueda vectorial (pgvector con índice HNSW) y el historial de identificaciones (tabla `identifications`). Cuando el catálogo supere ~50 000 registros conviene mover listados y búsqueda de texto a SQL (los índices `pg_trgm` ya están creados).

**Desvío respecto del pedido original, explicado**: se agregó la variable `DATABASE_URL`. El backend usa una conexión Postgres directa (psycopg + pool) en lugar de la API REST de Supabase porque necesita joins, transacciones atómicas para importar y operadores de pgvector. `SUPABASE_URL` + clave secreta se usan solo para Storage. La app Flutter nunca habla con Supabase.

## Flujo de una identificación

1. **App**: `image_picker` redimensiona a ≤2048 px y recomprime a JPEG (convierte HEIC en iOS). Valida tamaño (≤12 MB) y extensión. Envía `multipart/form-data` con el header `X-Client-Id` (UUID aleatorio de la instalación).
2. **API**: middleware rechaza cuerpos > límite antes de leerlos; limitador por cliente (10/min por defecto).
3. **Procesamiento** (`services/images/processing.py`): detecta el formato por contenido (JPEG, PNG, WEBP, HEIC/HEIF), protege contra imágenes gigantes, aplica orientación EXIF, convierte a RGB, redimensiona a 1536 px y **elimina todos los metadatos** (incluido GPS). Calcula nitidez (varianza del Laplaciano) para advertir fotos desenfocadas.
4. **Gemini** recibe el JPEG y un JSON Schema derivado de Pydantic; la respuesta se valida con el mismo modelo. Respuestas inválidas se descartan (`ai_bad_response`).
5. **OpenCLIP** genera un embedding de 512 dimensiones; pgvector busca las imágenes de catálogo más cercanas (solo imágenes aprobadas y del mismo modelo).
6. **GBIF** verifica los nombres propuestos (solo coincidencias `EXACT` cuentan como verificación).
7. **Catálogo**: se resuelve el taxón y sus ancestros (especie → género → familia → orden) contra los organismos del catálogo y se buscan relaciones en `fly_organism_matches`.
8. **Ranking** y **nivel de certeza** por reglas documentadas ([AI_PIPELINE.md](AI_PIPELINE.md)).
9. Se registra la identificación (sin la foto, salvo consentimiento + configuración explícita) y se devuelve JSON estructurado.

## Privacidad

- La foto del usuario **no se guarda** salvo que `ALLOW_USER_IMAGE_STORAGE=true` **y** el usuario envíe `store_image=true`. Se guarda en el bucket privado `user-uploads`.
- El id de instalación se guarda **hasheado con sal** (`CLIENT_HASH_SALT`); el historial solo se devuelve a quien presenta el mismo id.
- Los logs registran método, ruta, estado y duración. Nunca cuerpos, query strings, headers ni ids de cliente; un filtro enmascara claves y contraseñas por si aparecieran.

## API (prefijo `/api/v1`)

| Método y ruta | Descripción |
|---|---|
| `GET /health` | Liveness |
| `GET /ready` | Catálogo cargado, IA y embeddings configurados (no consume créditos) |
| `POST /identify/organism` | Función A (`image`, `store_image`; query `lang`) |
| `POST /identify/fly` | Función B (`image`, `store_image`; query `lang`, `country`) |
| `GET /organisms`, `GET /organisms/{id}` | Catálogo de organismos (filtros `q`, `group`, `order`, `family`, `rank`) |
| `GET /flies`, `GET /flies/{id}` | Catálogo de patrones (filtros `q`, `category`, `environment`) |
| `GET /flies/{id}/products` | Productos de un patrón (`country` ordena por envío) |
| `GET /products`, `GET /stores` | Comercio |
| `GET /search` | Búsqueda combinada |
| `GET /identifications`, `GET /identifications/{id}` | Historial del dispositivo (`X-Client-Id`) |

Errores siempre con forma `{"error": {"code", "message", "details"}}`. Códigos estables: `invalid_image`, `unsupported_format`, `image_too_small`, `image_too_large`, `rate_limited`, `analysis_unavailable`, `not_found`, `validation_error`…

## App Flutter

- `lib/core` (config, tema, errores de red) · `lib/models` (parseo JSON) · `lib/services` (API y selector de fotos, detrás de interfaces) · `lib/state` (Riverpod) · `lib/features/*` (pantallas) · `lib/widgets` (componentes reutilizables) · `lib/l10n` (ARB es/en).
- Las etapas de carga muestran solo lo que realmente ocurre: subida (con progreso real) y espera del servidor.
- Los códigos del backend (nivel, etapa, categoría…) se traducen en la app; un código desconocido se muestra tal cual, así una API más nueva no rompe una app vieja.
- Contrato API↔app: `backend/tests/test_contract_fixtures.py` genera los JSON de `mobile/test/fixtures/` desde el código real y falla si la forma cambia.

## Despliegue (preparado, no realizado)

`backend/Dockerfile` construye una imagen con torch CPU. Cualquier plataforma de contenedores sirve (Cloud Run, Fly.io, Render, Railway). Recomendaciones: ≥2 GB de RAM (OpenCLIP), `ENVIRONMENT=production` (activa validaciones estrictas), HTTPS obligatorio y un limitador compartido si hay más de una instancia.
