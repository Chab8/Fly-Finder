# Supabase paso a paso

Hasta completar esta guía, el backend funciona con el catálogo CSV en memoria (`CATALOG_BACKEND=memory`). Nada de lo que sigue es destructivo: las migraciones solo crean objetos.

## Qué hay en el repositorio

| Archivo | Contenido |
|---|---|
| `supabase/migrations/20261031000001_extensions_and_reference.sql` | Extensiones `vector` y `pg_trgm`, función `set_updated_at`, tablas de referencia `life_stages`, `image_sources`, `model_versions` con sus datos |
| `…000002_catalog.sql` | `organisms`, `organism_life_stages`, `common_names`, `organism_texts`, `taxonomic_synonyms`, `organism_images`, `fly_patterns`, `fly_pattern_texts`, `fly_pattern_materials`, `fly_pattern_variants`, `fly_images`, `fly_organism_matches` + índices (HNSW para vectores, trigramas para nombres) |
| `…000003_commerce.sql` | `stores`, `products`, `product_patterns` |
| `…000004_identifications.sql` | `identifications`, `identification_candidates` |
| `…000005_security_and_storage.sql` | RLS en todas las tablas, políticas de solo lectura del catálogo, buckets `catalog-images` (público) y `user-uploads` (privado) |

Estas migraciones ya se aplicaron con éxito sobre PostgreSQL 18 + pgvector local (los tests de `backend/tests/db/` lo hacen en cada ejecución). **Aún no se aplicaron en un proyecto Supabase real.**

### Por qué existe cada tabla adicional
- `organism_life_stages`: cada grupo usa etapas distintas (efímera: ninfa/dun/spinner; escarabajo: larva/pupa/adulto; pez: juvenil/adulto).
- `common_names`, `organism_texts`, `fly_pattern_texts`: separan el idioma de los datos científicos; agregar un idioma no cambia el esquema.
- `taxonomic_synonyms`: nombres antiguos o sinónimos que Gemini puede devolver.
- `fly_pattern_materials`, `fly_pattern_variants`: materiales y variantes como filas, no como JSON.
- `image_sources`: registro de fuentes y su política de uso comercial.
- `model_versions`: qué modelo generó cada embedding; evita mezclar vectores incompatibles.
- `identification_candidates`: candidatos rankeados en filas, para medir precisión con SQL.
- No se crearon `users`/`favorites`: no hay cuentas en el MVP (Supabase Auth ya provee `auth.users` cuando hagan falta).

## 1. Crear la cuenta y el proyecto

1. Entrá a https://supabase.com/dashboard y creá una cuenta (GitHub o email).
2. **New project** → elegí la organización.
3. **Name**: `fly-finder` (o el que quieras).
4. **Database Password**: generá una contraseña larga y guardala en tu gestor de contraseñas. La vas a necesitar para `DATABASE_URL`.
5. **Region**: elegí la más cercana a donde vas a correr el backend (no a los usuarios: la app habla con el backend, no con la base). Si vas a desplegar en EE. UU., `East US (North Virginia)`; para desarrollo desde Argentina, `South America (São Paulo)` reduce la latencia.
6. Plan Free alcanza para el MVP (500 MB de base, 1 GB de Storage). Ojo: los proyectos Free se pausan tras una semana sin actividad.
7. **Create new project** y esperá ~2 minutos.

## 2. Obtener los datos de conexión

Todos van en `backend/.env` (copiá antes `backend/.env.example` a `backend/.env`). **Nunca** en Flutter ni en git.

| Variable | Dónde está en el panel |
|---|---|
| `SUPABASE_URL` | Botón **Connect** (arriba) o **Settings → Data API** → `https://<ref>.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | **Settings → API Keys** → *Secret keys* → **Create new secret key** (empieza con `sb_secret_`). Una clave legacy `service_role` también funciona, pero Supabase deja de soportarlas a fines de 2026. |
| `DATABASE_URL` | Botón **Connect** → pestaña *Connection string* → **Session pooler** (puerto 5432). Reemplazá `[YOUR-PASSWORD]` por la contraseña del paso 1. Usá el *session pooler* porque la conexión directa solo funciona por IPv6. |

La clave secreta y la contraseña saltean RLS: tratalas como contraseñas. No las pegues en chats ni en issues.

## 3. Aplicar las migraciones

### Opción A — Supabase CLI (recomendada, ya instalada: v2.120)

```bash
cd /Users/manuchab/Fly-Finder && supabase login
```
Abre el navegador para autorizar la CLI.

```bash
supabase link --project-ref TU_PROJECT_REF
```
Vincula el repo con el proyecto. `TU_PROJECT_REF` es la parte `<ref>` de la URL. Te pide la contraseña de la base.

```bash
supabase db push --dry-run
```
Muestra qué migraciones aplicaría, sin aplicar nada. Deberías ver las 5.

```bash
supabase db push
```
Aplica las migraciones pendientes en orden y las registra para no repetirlas.

### Opción B — SQL Editor

En el panel: **SQL Editor → New query**. Abrí cada archivo de `supabase/migrations/` **en orden** (000001 → 000005), copiá todo el contenido, pegalo y presioná **Run**. Si un archivo falla, no sigas con el próximo; copiame el error.

pgvector se habilita dentro de la migración 000001 (`create extension vector with schema extensions`). No hace falta habilitarlo a mano.

## 4. Verificar

En **Table Editor** deberías ver 20 tablas en `public`, todas con el candado de RLS activo. En **Storage**: `catalog-images` (Public) y `user-uploads` (Private).

Desde la terminal:

```bash
cd /Users/manuchab/Fly-Finder/backend && .venv/bin/python -c "from app.core.config import get_settings; import psycopg; c=psycopg.connect(get_settings().database_url.get_secret_value()); print(c.execute('select count(*) from public.life_stages').fetchone())"
```
Debe imprimir `(11,)`.

## 5. Cargar el catálogo

```bash
cd /Users/manuchab/Fly-Finder && backend/.venv/bin/python scripts/import_organisms.py --apply
```

```bash
backend/.venv/bin/python scripts/import_fly_patterns.py --apply
```

Sin `--apply` los scripts solo validan. Son idempotentes: se pueden repetir sin duplicar.

## 6. Usar Supabase desde el backend

En `backend/.env` poné `CATALOG_BACKEND=postgres` y reiniciá uvicorn. `GET /api/v1/ready` debe mostrar `"backend": "postgres"` y `"organisms": 52`.

## Seguridad aplicada

- RLS activo en las 20 tablas. Rol `anon`/`authenticated`: solo lectura del catálogo; imágenes solo si `permission_status='approved'`; comercio solo activo; identificaciones solo propias (para cuando haya login). Ninguna escritura desde clientes.
- El backend usa la conexión de servidor (rol `postgres`), por eso la contraseña nunca sale de `backend/.env`.
- Funciones con `search_path` fijo (recomendación del linter de Supabase).
- Después de migrar, revisá **Advisors → Security** en el panel; debería no mostrar alertas críticas.
