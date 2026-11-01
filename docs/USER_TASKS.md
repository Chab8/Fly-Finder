# Tareas para vos

Actualizado: 2026-10-31 (segunda sesión). Las tareas están en orden de prioridad dentro de cada sección.

## ✅ Ya completado (no tenés que hacer nada)

- Monorepo: backend FastAPI, app Flutter (Android/iOS), migraciones Supabase, scripts, datos y documentación.
- **Supabase (hecho por vos)**: proyecto en us-east-1, las 5 migraciones aplicadas, catálogo importado (52 taxones, 69 patrones, 127 relaciones), buckets creados. Verificado con consultas de solo lectura.
- **Clave de Gemini (cargada por vos)** en `backend/.env`. **Probada con llamadas reales**: el backend identifica organismos y moscas.
- **Fotos del catálogo**: 89 de organismos (37 taxones, iNaturalist CC0/CC BY/CC BY-SA) y 21 de moscas (14 patrones, Wikimedia Commons), revisadas una por una, subidas al bucket `catalog-images` y con embeddings OpenCLIP en Supabase.
- **Set de evaluación**: 22 fotos con resultado esperado (`data/evaluation/manifest.csv`) y evaluación corrida con dos modelos de Gemini ([AI_PIPELINE.md](AI_PIPELINE.md#medición-con-gemini-real-2026-10-31-set-de-evaluación-de-22-fotos)).
- **App probada de punta a punta en el simulador iOS** con Gemini y Supabase reales: una larva de tricóptero (Hydropsychidae, verificada en GBIF, con moscas recomendadas) y una Woolly Bugger (coincidencia alta, qué imita, variantes).
- Tests: 136 backend + 20 Flutter, todos pasando.

## 🧭 Decisión pendiente — modelo de Gemini (siguiente paso)

Hoy `backend/.env` dice `GEMINI_MODEL=gemini-3.8-flash`. En la medición tardó entre 23 y 112 segundos por foto: con el límite de 45 s (hoy 60 s) muchas identificaciones se cortan y la app muestra solo similitud visual. `gemini-3.5-flash-lite` tarda unos 5 segundos, acierta el orden siempre, pero rara vez llega a familia.

**Mi recomendación**: usar Flash-Lite ahora para que la app sea usable, y volver a medir Flash más adelante (o con cuenta paga, donde la latencia suele ser menor).

1. Abrí `backend/.env` y cambiá la línea a:

```
GEMINI_MODEL=gemini-3.5-flash-lite
```

2. Reiniciá el backend y verificá en http://localhost:8000/api/v1/ready que diga `"model": "gemini-3.5-flash-lite"`.

Si preferís quedarte con Flash, subí `GEMINI_TIMEOUT_SECONDS=120` en `backend/.env` y en la app el tiempo de espera de lectura (`receiveTimeout`, hoy 130 s en `mobile/lib/services/fly_finder_api.dart`): las respuestas van a tardar más de un minuto.

## 🔑 Seguridad

### Rotar la clave de Gemini
La clave estuvo escrita en `backend/.env.example` (no llegó a GitHub) y quedó visible en una conversación. Por precaución:
1. Entrá a https://aistudio.google.com/apikey, creá una clave nueva y borrá la anterior.
2. Pegá la nueva solo en `backend/.env` (`GEMINI_API_KEY=`). No la pases por el chat.
3. Reiniciá el backend y verificá `/api/v1/ready` → `"ai": {"status": "configured"}`.

## ⚙️ Lo podés correr vos con un comando

Backend real (usa `backend/.env`):

```bash
cd /Users/manuchab/Fly-Finder/backend && .venv/bin/uvicorn app.main:create_app --factory --reload
```

App en el simulador iOS apuntando a ese backend:

```bash
cd /Users/manuchab/Fly-Finder/mobile && flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

Cómo probar las dos funciones en la app:
1. Cargá fotos de prueba en el simulador. Las del set de evaluación sirven:

```bash
xcrun simctl addmedia booted /Users/manuchab/Fly-Finder/data/evaluation/images/organisms/hydropsychidae_larva_0.jpg /Users/manuchab/Fly-Finder/data/evaluation/images/flies/woolly-bugger.jpg
```

2. **Identificar organismo** → *Elegir de la galería* → la larva → *Analizar foto*. Esperado: Hydropsychidae o Trichoptera, larva, moscas como Czech Nymph.
3. **Identificar mosca** → la Woolly Bugger. Esperado: Woolly Bugger, qué organismos imita y variantes.
4. En un iPhone real, el celular y la Mac tienen que estar en la misma red y `API_BASE_URL` tiene que ser la IP de la Mac (por ejemplo `http://192.168.0.10:8000`), no `localhost`.

Medir la calidad con Gemini real (22 llamadas):

```bash
cd /Users/manuchab/Fly-Finder && backend/.venv/bin/python scripts/evaluate.py --api http://localhost:8000 --lang es --out data/evaluation/report.json
```

Aceptar las licencias del SDK de Android (necesario para compilar para Android):

```bash
flutter doctor --android-licenses
```

## 🌐 Requiere una cuenta externa

### iNaturalist (solo lectura de condiciones)
Por qué: no pude abrir automáticamente su página oficial de prácticas recomendadas (responde 403).
1. Leé https://www.inaturalist.org/pages/api+recommended+practices y los Términos de uso enlazados ahí.
2. Confirmá: límite diario de solicitudes, límites de descarga de medios y si hay restricciones al uso comercial **de la API** (las fotos ya se filtran por licencia).
3. Si algo contradice lo documentado en [DATA_SOURCES.md](DATA_SOURCES.md), avisame y ajusto el cliente.

## 🧭 Otras decisiones

| Decisión | Opciones | Mi recomendación |
|---|---|---|
| Región del servidor | Donde alojes el backend | Misma región que Supabase (us-east-1) |
| ¿Guardar fotos de usuarios? | No (actual) / sí con consentimiento | **No** hasta tener política de privacidad; luego opt-in para mejorar el catálogo |
| Tier de Gemini | Free / pago | **Pago** antes de usuarios reales (en Free, Google puede usar los datos enviados) |
| Nombre comercial | — | Pendiente; `APP_NAME` lo cambia sin tocar código |
| Identificador de la app | `com.flyfinder.fly_finder` (provisorio) | Definilo antes de publicar (no se puede cambiar después en las tiendas) |

## 📷 Depende de fotografías o permisos

### 1. Fotos de moscas artificiales (lo más importante para la Función B)
Solo 14 de 69 patrones tienen foto. Commons no tiene más fotos útiles de los demás. Opciones: fotografiar tus propias moscas (3–5 fotos por patrón, fondo liso, distintos ángulos) o pedir permiso a atadores/fabricantes con la plantilla de [IMAGE_LICENSES.md](IMAGE_LICENSES.md). Cargalas en `data/catalog/fly_images.csv` con `source=own_photo` o `licensed_partner` y corré:

```bash
cd /Users/manuchab/Fly-Finder && backend/.venv/bin/python scripts/import_images.py --apply --upload && backend/.venv/bin/python scripts/generate_embeddings.py --target postgres --apply
```

### 2. Revisión experta
Pedile a un entomólogo o guía experimentado que revise:
- `data/catalog/fly_organism_matches.csv` (127 relaciones). Por cada relación confirmada: `expert_verified=true` y `verification_source=Nombre Apellido, AAAA-MM`.
- Las 89 fotos de `data/catalog/organism_images.csv`: las revisé a ojo (taxón plausible, estadio, sujeto visible), no es una revisión experta.
- Huecos que encontró la evaluación: no hay patrón para el imago (spinner) de Ephemeridae ni para cangrejos de río (Cambaridae solo tiene la Woolly Bugger).

### 3. Más fotos de organismos
Faltan 15 taxones sin foto. Para generar candidatas por estadio:

```bash
cd /Users/manuchab/Fly-Finder && backend/.venv/bin/python scripts/fetch_inaturalist_photos.py --per-taxon 3 --life-stage nymph --only Tricorythodes Caenidae
```

Revisalas según [DATA_IMPORT.md](DATA_IMPORT.md#fotos-de-inaturalist) antes de aprobarlas.

### 4. Tiendas y productos
Contactá tiendas (locales e internacionales). Cargá solo datos verificados con `data/import_templates/stores.csv` y `products.csv`: precio tal como figura en la tienda, su moneda y `last_verified_at`. Antes de automatizar precios, revisá los términos de cada tienda o pedí un feed autorizado.

## 🚀 Pendiente para producción

- Desplegar el backend (Dockerfile listo) con HTTPS, `ENVIRONMENT=production`, `CLIENT_HASH_SALT` aleatorio y ≥2 GB de RAM.
- Limitador de solicitudes compartido si hay más de una instancia (el actual es por proceso).
- Monitoreo de errores, latencia de Gemini y costos.
- Política de privacidad y términos de uso; formularios de privacidad de App Store y Google Play.
- Ícono, pantalla de inicio y nombre definitivos; cuentas de Apple Developer (USD 99/año) y Google Play Console (USD 25 única vez).
- Revisar el aviso legal de recomendaciones (las recomendaciones son orientativas).
- Supabase: revisar *Advisors* y activar backups (plan pago) antes del lanzamiento.
