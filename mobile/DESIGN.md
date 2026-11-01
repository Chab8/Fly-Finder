# Fly Finder — sistema de diseño

**Tesis:** un cuaderno de campo del pescador con mosca. La app identifica insectos y moscas, así que
habla como una guía de entomología: nombres científicos en serif cursiva, papel gris-niebla, verde de
río y latón para el equipo. Controles y texto corrido usan la tipografía del sistema para sentirse nativos.

**Firma (una sola):** el *anillo de pique* — los círculos que deja una trucha al tomar un insecto.
Aparece **solo** en el encabezado de Inicio (estático) y en la pantalla de análisis (animado,
se detiene con "Reducir movimiento"). No usarlo en ningún otro lado.

## Reglas

| Tema | Regla |
| --- | --- |
| Colores | Nunca hex en widgets. Usar `context.fly.*` (`FlyColors`, en `core/theme/app_theme.dart`). Cada rol tiene valor claro y oscuro. |
| Modo oscuro | Sigue el sistema (`ThemeMode.system`). No hay interruptor dentro de la app. |
| Verde de río | Solo acción principal, selección y estado. `river` = relleno; `accent` = texto/iconos sobre el fondo. |
| Latón (`brass`) | Significa **equipo**: tamaños de anzuelo, precios, tiendas. Nada más. |
| Tipografía | Serif (`SourceSerif4`) solo para títulos, nombres de patrón y binomios latinos (`context.serif`, `context.species`). Todo lo demás, fuente del sistema. |
| Tamaños | Cuerpo 17/15/13 pt; nunca menos de 12 pt. Nada de alturas ni anchos fijos para texto: la UI debe sobrevivir al tamaño de texto más grande. |
| Contraste | Texto ≥ 4.5:1; texto secundario y de niveles ≥ 7:1 / 5:1 (ver comentario en `FlyColors`). El estado nunca se comunica solo con color: siempre ícono + texto. |
| Táctil | Botones 56 pt; filas y tarjetas ≥ 44 pt. |
| Movimiento | Respetar `MediaQuery.disableAnimationsOf`. |
| Bordes | Líneas finas (`hairline`) en vez de sombras. Radios: tarjetas 16, controles 14, tarjeta de acción 22. |

## Paleta (contraste calculado sobre los hex)

| Rol | Claro | Oscuro |
| --- | --- | --- |
| canvas (niebla) | `#F2F4EE` | `#0E1512` |
| card | `#FFFFFF` | `#17211D` |
| ink | `#17211C` (14.9:1) | `#E8EDE6` (15.6:1) |
| inkSecondary | `#46524B` (7.4:1) | `#A9B5AD` (8.7:1) |
| river / onRiver | `#1B4332` / blanco (11.1:1) | `#2A6B55` / blanco (6.3:1) |
| accent | `#1B4332` | `#9AD8BC` |
| brass | `#7F5710` (6.4:1) | `#E0B45C` (8.5:1) |

## Tipografía

Source Serif 4 (Adobe, licencia SIL OFL 1.1) — 4 estilos en `assets/fonts/`. La licencia se
registra en la pantalla de licencias de la app (`main.dart`).
