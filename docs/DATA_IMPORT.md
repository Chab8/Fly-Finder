# Importación de datos

## Archivos

| Carpeta | Contenido |
|---|---|
| `data/catalog/` | Catálogo real curado (fuente de verdad). Lo leen el modo `memory` y los importadores |
| `data/demo/` | Registros **ficticios** para `DEMO_MODE` (todos `is_demo=true`, nunca se importan a producción) |
| `data/import_templates/` | Plantillas con encabezados, vocabularios permitidos y una fila de ejemplo ficticia |
| `data/review/` | Candidatas generadas por scripts para revisión humana (ignorado por git) |

Archivos reconocidos: `organisms.csv`, `fly_patterns.csv`, `fly_organism_matches.csv`, `organism_images.csv`, `fly_images.csv`, `stores.csv`, `products.csv`.

Convenciones: UTF-8, separador coma, encabezado obligatorio, líneas que empiezan con `#` son comentarios, celdas con varios valores separadas por `|`, booleanos `true/false`. Los vocabularios permitidos están al principio de cada plantilla.

## Claves naturales e identificadores

No escribís UUIDs: se derivan de forma determinística de claves naturales (`scientific_name` para organismos, `slug` para patrones, `store_slug + external_id` para productos). Reimportar actualiza en lugar de duplicar, y los ids son iguales en modo memoria y en Supabase.

## Flujo recomendado

```bash
cd /Users/manuchab/Fly-Finder && backend/.venv/bin/python scripts/validate_dataset.py
```
Valida esquema, vocabularios, duplicados (exactos y aproximados), referencias rotas, relaciones con etapas que el organismo no tiene, precios sin moneda o sin fecha de verificación, relaciones "verificadas" sin fuente. Sale con código 1 si hay errores.

```bash
backend/.venv/bin/python scripts/enrich_taxonomy.py --write --inaturalist
```
Verifica cada organismo contra GBIF (solo coincidencias exactas), completa la taxonomía y los ids, y marca `source_verified`. Informa diferencias, nunca sobrescribe en silencio.

```bash
backend/.venv/bin/python scripts/import_organisms.py --apply
```

```bash
backend/.venv/bin/python scripts/import_fly_patterns.py --apply
```
Importa patrones y relaciones (los organismos tienen que existir antes).

```bash
backend/.venv/bin/python scripts/import_products.py --apply
```

```bash
backend/.venv/bin/python scripts/import_images.py --apply --upload
```
Solo fotos `approved` con uso comercial permitido; `--upload` las copia al bucket público para no depender de servidores de terceros.

```bash
backend/.venv/bin/python scripts/generate_embeddings.py --target postgres --apply
```
Calcula embeddings una sola vez por imagen y modelo. Con `--target memory` genera `data/catalog/embeddings/<modelo>.npz` para el modo sin base de datos.

Todos los scripts que escriben son **dry-run por defecto** y escriben en una sola transacción: si algo falla, no queda nada a medias. Al reimportar un registro se reemplazan sus listas hijas (nombres comunes, textos, materiales, variantes); los embeddings nunca se tocan.

## Fotos de iNaturalist

```bash
backend/.venv/bin/python scripts/fetch_inaturalist_photos.py --per-taxon 3 --life-stage nymph --only Baetidae Perlidae
```
Escribe `data/review/organism_images_candidates.csv` (o el archivo de `--out`) con fotos CC0/CC BY/CC BY-SA de observaciones de grado investigación, una por observación, todas `pending`.

- `--life-stage` (`nymph`, `larva`, `pupa`, `adult`, `subimago`, `juvenile`, `egg`) usa la anotación de estadio de la comunidad de iNaturalist y precompleta `life_stage`. Para efímeras, "adult" se guarda como `imago`. Los taxones cuyo registro no tiene ese estadio se saltean.
- El cliente respeta 1 solicitud por segundo y reintenta los cortes de conexión y las respuestas 429/5xx.

Para cada fila: abrí la foto, confirmá que muestra ese taxón y ese estadio (descartá mudas/exuvias, capturas de pantalla, fotos donde el animal es diminuto y errores de la observación: en la revisión de 2026-10-31 aparecieron un ganso cargado como *Gammarus* y una trucha como Galaxiidae), cambiá a `approved` y copiala a `data/catalog/organism_images.csv`.

## Fotos de Wikimedia Commons

Commons tiene fotos de patrones clásicos con licencia libre por archivo. Usá la API (`action=query&prop=imageinfo&iiprop=url|extmetadata`) y quedate solo con `LicenseShortName` CC0, dominio público, CC BY o CC BY-SA. Wikimedia responde 403 si el User-Agent no trae un contacto real: `EXTERNAL_USER_AGENT` ya incluye la URL del proyecto. Guardá cada foto en `data/catalog/fly_images.csv` con `source=wikimedia_commons`, `source_id` = título del archivo, `source_url` = página del archivo y la atribución "Autor, licencia, via Wikimedia Commons". Descartá variantes con nombre propio (Adams Wulff, Crystal Stimulator) salvo que el catálogo tenga ese patrón.

## Estado del catálogo semilla (2026-10-31)

| Elemento | Cantidad | Estado |
|---|---|---|
| Organismos / taxones | 52 (efímeras, tricópteros, plecópteros, dípteros, odonatos, terrestres, crustáceos, anélidos, peces forraje) | 50 verificados contra GBIF. Textos y notas de pesca redactados a partir de referencias generales, **sin revisión experta** |
| Patrones de moscas | 69 (secas, ninfas, emergentes, streamers, terrestres, agua salada, atractores) | `unverified`: materiales y rangos de anzuelo son los publicados habitualmente; requieren revisión de un atador |
| Relaciones organismo↔mosca | 127 | Todas `expert_verified=false`, con la nota "pendiente de revisión experta" |
| Fotos de organismos | 89 de 37 taxones | iNaturalist (CC0/CC BY/CC BY-SA), revisadas una por una a ojo (taxón plausible, estadio, sujeto visible). **No es revisión experta** |
| Fotos de moscas | 21 de 14 patrones | Wikimedia Commons (dominio público/CC BY/CC BY-SA). Faltan 55 patrones: hacen falta fotos propias o con permiso |
| Tiendas y productos | 0 | No se inventaron. Cargalos con la plantilla cuando tengas datos verificados |

Deliberadamente **no** se completaron tamaños ni distribución geográfica: no hay una fuente citada todavía.

## Agregar registros nuevos

1. Copiá la fila de la plantilla correspondiente a `data/catalog/…` y borrá la fila de ejemplo.
2. `data_source` = de dónde sale el dato (libro, sitio con permiso, experto). `verification_status=unverified` hasta que alguien lo revise.
3. Para una relación verificada por un experto: `expert_verified=true` **y** `verification_source` con nombre o publicación (si no, la validación falla).
4. Validá, y luego importá.
