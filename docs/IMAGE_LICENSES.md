# Política de licencias de imágenes

Fly Finder apunta a ser un producto comercial. Una foto entra al catálogo **solo** si tenemos un derecho claro a mostrarla en una app comercial y la atribución correcta.

## Reglas

1. **Cada foto guarda su procedencia**: `source`, `source_id`, `source_url`, `license`, `attribution`, `commercial_use_allowed`, `permission_status`. Las columnas son obligatorias en la base.
2. **Solo se muestran fotos `approved`**. RLS en Supabase y el backend filtran todo lo demás.
3. **Importar ≠ aprobar**: los scripts proponen candidatas con `permission_status=pending`; una persona verifica contenido, licencia y atribución antes de aprobar.
4. **La atribución se muestra** bajo cada foto en la app ("Foto: autor · licencia").
5. **Nada se descarga de páginas web** sin licencia o permiso explícito, aunque la imagen sea accesible.

## Licencias

| Licencia | ¿Catálogo comercial? | Condición |
|---|---|---|
| CC0 / dominio público | Sí | Atribución recomendada |
| CC BY 4.0 (y versiones anteriores) | Sí | Atribución obligatoria |
| CC BY-SA | Sí, con cuidado | Atribución; si se adapta la imagen (recorte creativo, montaje), la adaptación hereda la licencia. Redimensionar no es adaptar |
| CC BY-ND | **No por defecto** | Sin obras derivadas; recortar para la app es una zona gris |
| CC BY-NC, BY-NC-SA, BY-NC-ND | **No** | Solo uso no comercial |
| Sin licencia / "todos los derechos reservados" | **No** | Solo con permiso escrito |
| Permiso escrito de fabricante, atador o tienda | Sí | Guardar el permiso (fecha, alcance, firmante) y referenciarlo en `license` |
| Foto propia | Sí | `source=own_photo` |

La política está implementada en `backend/app/services/taxonomy/licenses.py` y la usa el script de iNaturalist.

## Entrenamiento de modelos

No entrenamos modelos en el MVP. Generar **embeddings** de fotos del catálogo para búsqueda de similitud es un uso técnico de la imagen; aun así, si un permiso o licencia excluye explícitamente el uso con IA o aprendizaje automático, marcá esa foto con `permission_status=rejected` o no la importes. Antes de cualquier ajuste fino o entrenamiento futuro se necesita una revisión legal específica.

## Fotos de usuarios

- No se guardan por defecto (`ALLOW_USER_IMAGE_STORAGE=false`).
- Si en el futuro se activa, requiere: consentimiento explícito por foto (`store_image=true`), texto de consentimiento en la app, política de privacidad publicada y plazo de borrado. Nunca se usan para el catálogo sin un segundo consentimiento.

## Pedir permiso a fabricantes, atadores y tiendas

Plantilla mínima del pedido (adaptala):
> Solicitamos permiso no exclusivo para mostrar las fotografías [lista/URL] en la aplicación Fly Finder (iOS/Android, uso comercial, mundial), con la atribución "[nombre]" y enlace a [sitio]. Las imágenes podrán redimensionarse y usarse para búsqueda por similitud visual dentro de la app. No se usarán para entrenar modelos de IA. El permiso puede revocarse con 30 días de aviso.

Guardá la respuesta y cargá en `fly_images.csv`: `source=licensed_partner`, `license=Permiso escrito AAAA-MM-DD`, `attribution`, `commercial_use_allowed=true`, `permission_status=approved`.
