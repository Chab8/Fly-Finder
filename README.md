# Fly Finder (nombre de trabajo)

Aplicación móvil mundial para pesca con mosca que conecta organismos reales con moscas artificiales:

- **Función A — Identificar un organismo**: foto de un insecto, crustáceo, pez forraje, etc. → identificación taxonómica (al nivel que la foto justifique) → moscas que lo imitan, ordenadas y explicadas.
- **Función B — Identificar una mosca**: foto de una mosca artificial → patrón probable y alternativas → qué organismos imita → variantes y productos.

Agua dulce y salada, tiendas locales e internacionales, español e inglés. "Fly Finder" es un nombre provisional configurable (`APP_NAME`).

> Estado: **MVP ejecutable, probado con Gemini y Supabase reales** (2026-10-31): la app identifica organismos y moscas de punta a punta en el simulador iOS. Catálogo con 110 fotos con licencia. Pendiente: elegir el modelo de Gemini por latencia, fotos de más patrones y revisión experta — ver [docs/USER_TASKS.md](docs/USER_TASKS.md).

## Tecnologías

| Capa | Tecnología |
|---|---|
| App móvil | Flutter 3.47 · Riverpod 3 · GoRouter 18 · Dio · image_picker · gen-l10n (es/en) |
| API | Python 3.12 · FastAPI · Pydantic 2 |
| Base de datos | Supabase PostgreSQL + pgvector + Storage, migraciones en `supabase/migrations` |
| Visión | Gemini API (`GEMINI_MODEL`: `gemini-3.8-flash` o `gemini-3.5-flash-lite`, salida JSON validada con Pydantic) |
| Similitud visual | OpenCLIP ViT-B-32 / laion2b_s34b_b79k (MIT), 512 dimensiones |
| Taxonomía | GBIF Species API (validación de nombres), iNaturalist (herramientas de catálogo) |

## Estructura

```
backend/            API FastAPI (app/), tests/, requirements*.txt, .env.example, Dockerfile
mobile/             App Flutter (lib/, test/)
supabase/           config.toml y migrations/ (SQL reproducible)
scripts/            Importadores, validación, embeddings, evaluación
data/catalog/       Catálogo curado real (CSV)          data/demo/  Datos FICTICIOS para modo DEMO
data/import_templates/  Plantillas CSV                  data/evaluation/  Set de evaluación
docs/               Documentación (ver índice abajo)
```

## Puesta en marcha rápida (sin credenciales, modo DEMO)

Requisitos ya presentes en esta Mac: Python 3.12 (`/opt/homebrew/bin/python3.12`), Flutter 3.47, Xcode 27.

```bash
cd backend && /opt/homebrew/bin/python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt -r requirements-ml.txt
```

Levantar la API en modo DEMO (datos ficticios, sin IA real, claramente rotulado):

```bash
cd backend && DEMO_MODE=true .venv/bin/uvicorn app.main:create_app --factory --reload
```

Documentación interactiva: http://localhost:8000/docs · Estado: http://localhost:8000/api/v1/ready

Ejecutar la app en el simulador de iOS (en otra terminal):

```bash
cd mobile && flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

En el emulador de Android la app usa `http://10.0.2.2:8000` por defecto. En un teléfono físico usá la IP de tu Mac en la red local (`--dart-define=API_BASE_URL=http://192.168.x.x:8000`) y levantá uvicorn con `--host 0.0.0.0`.

## Configuración

Toda la configuración del backend está en `backend/.env` (copiá `backend/.env.example`). La app **no tiene secretos**: solo recibe `API_BASE_URL` y `APP_NAME` por `--dart-define`. Detalle de cada variable en [docs/API_SETUP.md](docs/API_SETUP.md).

| Modo | Cómo | Para qué |
|---|---|---|
| DEMO | `DEMO_MODE=true` | Probar la interfaz sin claves. Todo resultado se marca como ficticio. |
| Real, catálogo local | `GEMINI_API_KEY` + `CATALOG_BACKEND=memory` | IA real con el catálogo CSV, sin base de datos. |
| Real, Supabase | `CATALOG_BACKEND=postgres` + `DATABASE_URL` | Configuración de staging/producción. |

## Tests

```bash
cd backend && .venv/bin/python -m pytest
```

```bash
cd mobile && flutter test
```

Los tests de base de datos usan un PostgreSQL local temporal con pgvector (se saltean si no está instalado). El test con el modelo OpenCLIP real se activa con `RUN_ML_TESTS=1`. Ver [docs/TESTING.md](docs/TESTING.md).

## Documentación

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — componentes, flujo de imágenes, decisiones técnicas
- [AI_PIPELINE.md](docs/AI_PIPELINE.md) — los dos motores, niveles de certeza, ranking
- [DATABASE_SETUP.md](docs/DATABASE_SETUP.md) — Supabase paso a paso
- [API_SETUP.md](docs/API_SETUP.md) — Gemini y demás proveedores, costos, variables
- [DATA_SOURCES.md](docs/DATA_SOURCES.md) · [IMAGE_LICENSES.md](docs/IMAGE_LICENSES.md) · [DATA_IMPORT.md](docs/DATA_IMPORT.md)
- [TESTING.md](docs/TESTING.md) — pruebas y evaluación de calidad
- [USER_TASKS.md](docs/USER_TASKS.md) — **lo que tenés que hacer vos, paso a paso**
