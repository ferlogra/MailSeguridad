# Sesión de desarrollo — v1.14.0 a v1.15.2

**Fecha**: 17 de junio de 2026

## Resumen

En esta sesión se implementaron las siguientes funcionalidades y mejoras en MailSeguridad:

### v1.14.0 — Botones de búsqueda + Unificación Act. Tickets

- Añadidos botones 🔍 junto a 5 campos del detalle de mensaje (`to`, `internet_message_id`, `conversation_id`, `cs_relacionado`, `inc_relacionado`) para buscar mensajes con el mismo valor.
- Creado endpoint API `mensajes_by_field_api` y modal con tabla de 10 columnas (resultados limitados a 100).
- Añadida pantalla "Actuaciones de Tickets" (Opción A) con LEFT JOIN entre Mensajes y Actuaciones, reutilizando `mensajes_list.html`.

### v1.14.1 — Corrección de TemplateSyntaxError

- Corregido bloque `{% if is_admin %}` sin cerrar en `mensaje_detail.html` que provocaba TemplateSyntaxError al guardar.

### v1.14.2 — Botón de búsqueda a la derecha del campo

- Los botones 🔍 se movieron de debajo del campo a la derecha del mismo usando un contenedor flex `.field-row`.
- CSS añadido: `display: flex; flex-direction: row; align-items: center`.

### v1.15.0 — Refactor: reutilizar pantalla Mensajes completa

- **Eliminado** `mensajes_by_field_api` — ya no es necesaria.
- **Eliminado** modal custom con tabla simple (10 columnas, sin paginación, sin ordenación, máx 100 resultados).
- **Añadido** filtro `field` + `value` a `mensajes_list_view` con whitelist de 5 campos permitidos.
- Los botones 🔍 ahora abren `/mensajes/?field=X&value=Y` en una nueva pestaña, reutilizando el 100% de la funcionalidad existente (column-selector, ordenación multi-columna, paginación, filtros avanzados, URL compartible).

### v1.15.1 — Campo Cuerpo a ancho completo

- Movido el campo `body` al final del grid de campos.
- Añadida clase CSS `.detail-field-fullwidth` con `grid-column: 1 / -1`.
- El textarea del cuerpo ocupa las dos columnas del formulario con altura mínima de 12rem.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `MailSeguridad/seguridad/views.py` | +field/value filter en mensajes_list_view; -mensajes_by_field_api; body al final de editable_fields |
| `MailSeguridad/seguridad/urls.py` | -ruta mensajes-by-field/ |
| `MailSeguridad/templates/seguridad/mensaje_detail.html` | +botones 🔍 + .field-row + body full-width; -modal search |
| `MailSeguridad/templates/seguridad/mensajes_list.html` | Usada por la nueva ruta Act. Tickets (Opción A) |
| `MailSeguridad/MailSeguridad/version.py` | Actualizado a 1.15.2 |

## Versiones generadas

- `v1.14.0` — Botones 🔍 + unificación Act. Tickets
- `v1.14.1` — Fix TemplateSyntaxError
- `v1.14.2` — Botón a la derecha del campo
- `v1.15.0` — Refactor: reutilizar pantalla Mensajes
- `v1.15.1` — Cuerpo a ancho completo
- `v1.15.2` — Actualización de documentación y versión
