# Proveedores externos y variables de entorno

## Dónde va cada variable

Todas en **`backend/.env`** (copiá `backend/.env.example`). El archivo está en `.gitignore`. La app Flutter solo recibe por `--dart-define` valores públicos: `API_BASE_URL` y `APP_NAME`.

| Variable | Obligatoria | Valor |
|---|---|---|
| `ENVIRONMENT` | no | `development` · `staging` · `production` (en producción exige Postgres, sal y sin DEMO) |
| `CATALOG_BACKEND` | no | `memory` (CSV) o `postgres` |
| `DEMO_MODE` | no | `true` solo para probar la interfaz |
| `GEMINI_API_KEY` | para IA real | Clave de Google AI Studio |
| `GEMINI_MODEL` | no | `gemini-3.8-flash` (por defecto) |
| `GEMINI_TIMEOUT_SECONDS` | no | 45 |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL` | con Supabase | ver [DATABASE_SETUP.md](DATABASE_SETUP.md) |
| `EMBEDDINGS_ENABLED`, `OPENCLIP_MODEL`, `OPENCLIP_PRETRAINED`, `OPENCLIP_DEVICE` | no | `true`, `ViT-B-32`, `laion2b_s34b_b79k`, `cpu` (`mps` en Mac) |
| `EXTERNAL_USER_AGENT` | recomendado | `FlyFinder/0.1 (contact: tu-email)`; GBIF e iNaturalist piden identificarse |
| `CORS_ORIGINS` | no | Orígenes web permitidos; la app móvil no lo necesita |
| `MAX_UPLOAD_MB`, `IDENTIFY_RATE_LIMIT_PER_MINUTE` | no | 12, 10 |
| `ALLOW_USER_IMAGE_STORAGE` | no | `false`. Decisión de producto pendiente |
| `CLIENT_HASH_SALT` | en producción | Cadena aleatoria larga |
| `API_BASE_URL` | Flutter | `--dart-define=API_BASE_URL=https://api.tu-dominio` |

## Gemini (Google AI Studio)

### Por qué
Es el motor que interpreta la foto. Sin clave, la API responde igual pero solo con similitud visual y lo advierte.

### Pasos
1. Entrá a https://aistudio.google.com/ con tu cuenta de Google y aceptá los términos.
2. Menú izquierdo **Get API key** (o directo https://aistudio.google.com/apikey) → **Create API key**.
3. Elegí un proyecto de Google Cloud existente o **Create API key in new project** (`fly-finder`).
4. Copiá la clave (empieza con `AIza…`) y pegala en `backend/.env`:
   `GEMINI_API_KEY=AIza...` — no la mandes por chat ni la subas a git.
5. **Facturación**: en **Projects** (https://aistudio.google.com/projects) ves el tier del proyecto. Para pasar de Free a Tier 1 hay que **vincular una cuenta de facturación activa**; según la documentación, el cambio es automático e instantáneo.
6. **Límites**: tus límites reales están en https://aistudio.google.com/rate-limit. La documentación no publica cifras RPM/RPD por modelo; se ven por proyecto.
7. Reiniciá el backend y verificá: `GET /api/v1/ready` → `"ai": {"status": "configured"}`.
8. Prueba real con una foto (consume una llamada):

```bash
curl -s -F image=@/ruta/a/una/foto.jpg "http://localhost:8000/api/v1/identify/organism?lang=es" | python3 -m json.tool | head -60
```
Si Gemini respondió, verás `"ai_available": true` y `"ai_model": "gemini-3.8-flash"`. Si la respuesta no cumple el esquema, el backend la descarta y verás la advertencia `ai_bad_response` (eso también es una verificación del esquema).

### Importante: privacidad y costos
- **En el tier gratuito, Google puede usar los datos enviados para mejorar sus productos** (página de precios, consultada 2026-10-31). Con facturación activa, no. Para fotos de usuarios reales conviene usar el tier pago.
- Precios estándar `gemini-3.8-flash` (consultados 2026-10-31): **USD 0,75 / 1M tokens de entrada** y **USD 3,75 / 1M de salida** hasta el 31-12-2026; **USD 1,50 y 7,50 desde el 1-1-2027**. `gemini-3.5-flash-lite`: USD 0,30 / 2,50.
- Estimación por identificación (a validar con uso real): imagen 1536 px ≈ 4 tiles × 258 = ~1 000 tokens + prompt y esquema ~1 500 → ~2 500 tokens de entrada; salida ~1 000–1 500 (incluye "thinking"). ≈ **USD 0,006–0,008** por identificación en 2026 y el doble en 2027. 1 000 identificaciones diarias ≈ USD 6–8/día (2026).
- Los límites gratuitos no alcanzan para producción.

## GBIF

- API pública, **sin clave** para lectura. Endpoints usados: `GET /v1/species/match` (verificación de nombres) y `/species/search` (herramientas). Verificados funcionando el 2026-10-31.
- Se envía `User-Agent` identificable y se cachean respuestas 24 h.
- Detalle de datos y licencias: [DATA_SOURCES.md](DATA_SOURCES.md).

## iNaturalist

- Solo se usa en scripts del catálogo (no en cada identificación). Sin clave para lectura.
- El cliente limita a **1 solicitud por segundo**. La práctica recomendada citada por clientes oficiales y el foro es ≤60/min; hay reportes de errores 429 incluso a ese ritmo.
- La API pública **no** da acceso al modelo de visión de iNaturalist.

## OpenCLIP

- Sin clave. Los pesos (~600 MB) se descargan de Hugging Face la primera vez y quedan en caché (`~/.cache/huggingface`).
- Probado en esta Mac: genera vectores de 512 dimensiones normalizados (`RUN_ML_TESTS=1`).
- En servidores pequeños se puede apagar con `EMBEDDINGS_ENABLED=false`.
