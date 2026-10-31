# Fuentes de datos

Regla general: **nada de scraping no autorizado**. Toda fuente se usa por su API pública documentada o con permiso escrito, y cada registro guarda su procedencia (`data_source`, `source`, `source_url`, `license`, `attribution`).

| Fuente | API | Clave | Qué aporta | Qué podemos guardar | Imágenes | Uso comercial |
|---|---|---|---|---|---|---|
| **GBIF** | REST `api.gbif.org/v1` (Species, Occurrence) | No (lectura) | Nombres aceptados, jerarquía taxonómica, ids de taxón, ocurrencias | Ids y taxonomía, citando GBIF | Por registro de ocurrencia, licencia de cada institución | Backbone: citar GBIF. Ocurrencias: según licencia de cada dataset (CC0, CC BY o CC BY-NC); filtrar NC |
| **iNaturalist** | REST `api.inaturalist.org/v1` | No (lectura) | Taxones, nombres comunes, observaciones geolocalizadas, fotos | Ids de taxón; metadatos de fotos con licencia | Licencia **por foto** (`license_code`); `null` = todos los derechos reservados | Solo CC0, CC BY, CC BY-SA. La opción por defecto de iNaturalist es CC BY-NC, así que muchas fotos **no** sirven |
| **Gemini** | Google AI | Sí | Interpretación de fotos | No se guarda su salida como dato del catálogo; solo en el historial de identificaciones | — | Según términos de Google; en tier gratuito los datos pueden usarse para mejorar productos |
| **Troutnut.com** | Sin API pública | — | Referencia entomológica de alta calidad | **Nada sin permiso** | Derechos de sus autores | Requiere acuerdo escrito |
| **IdentaFly** (my.identafly.app) | Sin API pública documentada | — | Relaciones insecto↔mosca | **Nada sin permiso** | Derechos de sus autores | Requiere acuerdo escrito |
| **Fabricantes, atadores, tiendas** | Variable | — | Fotos de moscas, productos, precios | Lo que autoricen por escrito | Solo con permiso | Acuerdo escrito (ver [IMAGE_LICENSES.md](IMAGE_LICENSES.md)) |
| **Wikimedia Commons** | API MediaWiki | No | Fotos con licencia libre | Metadatos y archivos con licencia compatible | Por archivo | CC0 / CC BY / CC BY-SA sí; verificar cada archivo |

## Cómo se usan hoy

- **Taxonomía del catálogo**: `scripts/enrich_taxonomy.py` verificó los 52 organismos contra el GBIF Backbone el 2026-10-31. 50 coincidieron exactamente (`source_verified`, con `gbif_taxon_id` e `inaturalist_taxon_id`). Dos no:
  - *Brachyura*: GBIF la clasifica como familia; es un infraorden. Se mantuvo el rango correcto, sin id GBIF.
  - *Hirudinea* (sanguijuelas): no existe en el Backbone (GBIF propone un género de aves). Queda sin verificar.
  - GBIF corrigió dos órdenes: Cottidae → Scorpaeniformes, Galaxiidae → Osmeriformes.
- **En cada identificación**: GBIF verifica los nombres que propone Gemini (con caché de 24 h).
- **Fotos**: `scripts/fetch_inaturalist_photos.py` **propone** fotos con licencia comercial para revisión humana; no descarga ni importa nada.

## Límites y condiciones a respetar

- **GBIF**: sin límite numérico publicado para la API de lectura; uso razonable, `User-Agent` identificable, citar GBIF y los datasets usados. Descargas masivas solo por el servicio oficial de descargas (con DOI), nunca paginando la API.
- **iNaturalist**: ≤1 solicitud/segundo (el cliente lo impone), `User-Agent` identificable, sin descargas masivas de fotos. **Pendiente para vos**: leer la página oficial "API Recommended Practices" y los Términos de uso (no pudimos acceder automáticamente) y confirmar límites diarios y condiciones de uso comercial de la API. Ver [USER_TASKS.md](USER_TASKS.md).
- **Gemini**: cuotas por proyecto en AI Studio; costos en [API_SETUP.md](API_SETUP.md).

## Datos que todavía faltan

- Tamaños (mm) de organismos con fuente citable.
- Distribución geográfica por taxón (se puede derivar de ocurrencias GBIF agregadas por país).
- Fotos autorizadas de organismos y, sobre todo, de moscas artificiales.
- Revisión experta de relaciones organismo↔mosca y de datos de patrones.
- Tiendas y productos reales con permiso o con fuente verificada.
