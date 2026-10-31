# Tareas para vos

Actualizado: 2026-10-31. Las tareas están en orden de prioridad dentro de cada sección.

## ✅ Ya completado (no tenés que hacer nada)

- Monorepo creado: backend FastAPI, app Flutter (Android/iOS), migraciones Supabase, scripts, datos y documentación.
- Backend completo: 14 endpoints `/api/v1`, dos motores de identificación, ranking, comercio, historial, validación de imágenes, rate limit, logs seguros, modo DEMO.
- Gemini integrado (adaptador listo, **sin probar con una clave real**: falta tu clave).
- OpenCLIP instalado y **probado con el modelo real** en esta Mac.
- GBIF integrado y **probado en vivo**: 50 de 52 organismos verificados.
- 5 migraciones SQL **aplicadas y probadas** sobre PostgreSQL 18 + pgvector local (no todavía sobre Supabase).
- Catálogo semilla: 52 taxones, 69 patrones, 127 relaciones (pendientes de revisión experta).
- App Flutter: 9 pantallas, español/inglés, probada en simulador iOS contra el backend local.
- Tests: 123 backend + 20 Flutter, todos pasando.
- Se instaló `pgvector` con Homebrew (`brew install pgvector`) para probar migraciones localmente.

## ⚙️ Lo podés correr vos con un comando (sin cuentas)

Levantar la API en modo DEMO y abrir la app (ver [README](../README.md)):

```bash
cd /Users/manuchab/Fly-Finder/backend && DEMO_MODE=true .venv/bin/uvicorn app.main:create_app --factory --reload
```

```bash
cd /Users/manuchab/Fly-Finder/mobile && flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

Aceptar las licencias del SDK de Android (necesario para compilar para Android; `flutter doctor` lo marca como pendiente). Te va a pedir confirmar cada licencia con `y`:

```bash
flutter doctor --android-licenses
```

Instalar Java no hace falta: Android Studio trae su propio JDK. Si `flutter build apk` se queja de Java, abrí Android Studio una vez.

## 🔑 Requiere una API key

### 1. Gemini — **siguiente paso exacto**
Por qué: sin esto no hay identificación real; la app responde solo con similitud visual.
1. Seguí [API_SETUP.md → Gemini](API_SETUP.md#gemini-google-ai-studio) (crear clave en https://aistudio.google.com/apikey).
2. Creá el archivo de configuración:

```bash
cp /Users/manuchab/Fly-Finder/backend/.env.example /Users/manuchab/Fly-Finder/backend/.env
```

3. Abrí `backend/.env` con tu editor y completá `GEMINI_API_KEY=`. No me la pases por el chat.
4. Levantá el backend **sin** DEMO y verificá: http://localhost:8000/api/v1/ready → `"ai": {"status": "configured"}`.
5. Probá con una foto real de un insecto (comando en API_SETUP.md). Avisame el resultado; reviso juntos la calidad de la respuesta y ajusto el prompt si hace falta.

Verificación de éxito: la respuesta trae `"ai_available": true`, un candidato y advertencias coherentes.

## 🌐 Requiere una cuenta externa

### 2. Supabase
Por qué: base de datos persistente, historial real, Storage para fotos del catálogo y búsqueda vectorial en producción.
Seguí [DATABASE_SETUP.md](DATABASE_SETUP.md) completo (crear proyecto → claves en `backend/.env` → `supabase db push` → importar catálogo → `CATALOG_BACKEND=postgres`).
Nota: hay un conector de Supabase disponible en esta sesión. Si preferís, una vez creado el proyecto puedo aplicar las migraciones por ahí, pero solo con tu confirmación explícita.

### 3. iNaturalist (solo lectura de condiciones)
Por qué: no pude abrir automáticamente su página oficial de prácticas recomendadas (responde 403).
1. Leé https://www.inaturalist.org/pages/api+recommended+practices y los Términos de uso enlazados ahí.
2. Confirmá: límite diario de solicitudes, límites de descarga de medios y si hay restricciones al uso comercial **de la API** (las fotos ya se filtran por licencia).
3. Si algo contradice lo documentado en [DATA_SOURCES.md](DATA_SOURCES.md), avisame y ajusto el cliente.

## 🧭 Requiere tu decisión

| Decisión | Opciones | Mi recomendación |
|---|---|---|
| Región del servidor | Donde alojes el backend y Supabase | Misma región para ambos; EE. UU. Este si apuntás a un público global |
| ¿Guardar fotos de usuarios? | No (actual) / sí con consentimiento | **No** hasta tener política de privacidad; luego opt-in para mejorar el catálogo |
| Modelo de Gemini | `gemini-3.8-flash` / `gemini-3.5-flash-lite` | Empezar con 3.8 Flash y medir con el set de evaluación; probar Flash-Lite para bajar costos |
| Tier de Gemini | Free / pago | **Pago** antes de usuarios reales (en Free, Google puede usar los datos enviados) |
| Nombre comercial | — | Pendiente; `APP_NAME` lo cambia sin tocar código |
| Identificador de la app | `com.flyfinder.fly_finder` (provisorio) | Definilo antes de publicar (no se puede cambiar después en las tiendas) |

## 📷 Depende de fotografías o permisos

### 4. Fotos de organismos
1. Generá candidatas con licencia comercial:

```bash
cd /Users/manuchab/Fly-Finder && backend/.venv/bin/python scripts/fetch_inaturalist_photos.py --per-taxon 5 --only Baetidae Heptageniidae Chironomidae Hydropsychidae Perlidae
```

2. Revisá `data/review/organism_images_candidates.csv` según [DATA_IMPORT.md](DATA_IMPORT.md#fotos-de-inaturalist) y aprobá las correctas.
3. Importá y generá embeddings (comandos en DATA_IMPORT.md).

### 5. Fotos de moscas artificiales (crítico para la Función B)
No existe una fuente libre confiable. Opciones: fotografiar tus propias moscas (lo más rápido: 3–5 fotos por patrón, fondo liso, distintos ángulos) o pedir permiso a atadores/fabricantes con la plantilla de [IMAGE_LICENSES.md](IMAGE_LICENSES.md). Cargalas en `data/catalog/fly_images.csv` con `source=own_photo` o `licensed_partner`.

### 6. Revisión experta
Pedile a un entomólogo o guía experimentado que revise `data/catalog/fly_organism_matches.csv` (127 relaciones) y los rangos de anzuelo de `fly_patterns.csv`. Por cada relación confirmada: `expert_verified=true` y `verification_source=Nombre Apellido, AAAA-MM`.

### 7. Set de evaluación
Juntá fotos fuera del catálogo y completá `data/evaluation/manifest.csv` ([TESTING.md](TESTING.md#evaluación-real-del-reconocimiento)).

### 8. Tiendas y productos
Contactá tiendas (locales e internacionales). Cargá solo datos verificados con `data/import_templates/stores.csv` y `products.csv`: precio tal como figura en la tienda, su moneda y `last_verified_at`. Antes de automatizar precios, revisá los términos de cada tienda o pedí un feed autorizado.

## 🚀 Pendiente para producción

- Desplegar el backend (Dockerfile listo) con HTTPS, `ENVIRONMENT=production`, `CLIENT_HASH_SALT` aleatorio y ≥2 GB de RAM.
- Limitador de solicitudes compartido si hay más de una instancia (el actual es por proceso).
- Monitoreo de errores y costos (Gemini reporta tokens por respuesta; agregar métricas).
- Política de privacidad y términos de uso; formularios de privacidad de App Store y Google Play.
- Ícono, pantalla de inicio y nombre definitivos; cuentas de Apple Developer (USD 99/año) y Google Play Console (USD 25 única vez).
- Revisar el aviso legal de recomendaciones (las recomendaciones son orientativas).
- Supabase: revisar *Advisors* y activar backups (plan pago) antes del lanzamiento.
