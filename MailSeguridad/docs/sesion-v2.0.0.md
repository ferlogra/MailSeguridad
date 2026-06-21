# Sesión v2.0.0 — Actuaciones many-to-many

## Resumen

Migración de la relación `Actuacion → Mensaje` de **1:N** (campo `Actuacion.mensaje` como TextField) a **N:N** mediante tabla intermedia `ActuacionMensaje` (modelo `ActuacionMensaje`, tabla `ActuacionesMensajes`).

## Cambios principales

### Modelos
- **Nuevo modelo** `ActuacionMensaje` (`seguridad/models.py:199`):
  - `id_actuacion_mensaje` (PK auto)
  - `actuacion` (FK → `Actuacion`, `on_delete=CASCADE`, `related_name="aplicaciones"`)
  - `mensaje` (TextField — almacena `InternetMessageId`)
  - `fecha_hora` (DateTimeField — cuándo se aplicó)
  - Meta: `db_table = "ActuacionesMensajes"`, ordenado por `-fecha_hora`.
- **Eliminado** el campo `Actuacion.mensaje` (antes era un TextField nullable).
- El campo `Actuacion.id_tipo_actuacion` ahora usa `on_delete=PROTECT` (era `SET_NULL`).

### Migración (`0006_remove_actuacion_mensaje_actuacionmensaje.py`)
1. Crea la tabla `ActuacionesMensajes`.
2. Migración de datos: para cada `Actuacion` con `mensaje` no nulo, inserta un registro en `ActuacionMensaje` con `actuacion_id=id_actuacion`, `mensaje=mensaje`, `fecha_hora=fecha_hora`.
3. Elimina el campo `mensaje` de `Actuaciones`.

### APIs refactorizadas
- **`actuaciones_por_mensaje_api`**: ahora filtra mediante `Actuacion.objects.filter(aplicaciones__mensaje=mensaje_id)` en lugar del campo directo.
- **`actuaciones_recientes_api`** (nueva): devuelve últimas 15 actuaciones distintas NO aplicadas aún al mensaje.
- **`actuacion_create_api`**: ya no guarda `mensaje` en `Actuacion`; si se proporciona, crea un `ActuacionMensaje`.
- **`actuacion_aplicar_api`** (nueva): aplica actuación existente a otro mensaje sin duplicarla.

### SQL de Act. Tickets
La vista `actuaciones_tickets_view` ahora usa `LEFT JOIN ActuacionesMensajes ON ...` en lugar de la columna directa `Actuaciones.Mensaje`.

### Interfaz de usuario (modal de actuaciones)
- Nuevo panel "Reusar actuaciones" que carga actuaciones recientes vía `actuaciones_recientes_api`.
- Botón "Aplicar" (antes "Copiar") que crea un vínculo en `ActuacionMensaje` en lugar de duplicar la actuación.

### Admin de Django
- `ActuacionAdmin`: se añadió `ActuacionMensajeInline` (muestra los mensajes asociados).
- `ActuacionMensajeAdmin`: registro independiente para gestionar la tabla intermedia.

## Archivos afectados

| Archivo | Cambio |
|---------|--------|
| `seguridad/models.py` | Nuevo modelo `ActuacionMensaje`, eliminado `Actuacion.mensaje` |
| `seguridad/migrations/0006_*.py` | Migración de esquema + datos |
| `seguridad/views.py` | Nuevas APIs y refactor de existentes |
| `seguridad/urls_actuaciones.py` | Nuevas rutas para APIs |
| `seguridad/admin.py` | Inlines y admin de ActuacionMensaje |
| `templates/base.html` | Ajustes en modal JS para "Aplicar" |
| `MailSeguridad/version.py` | bump a v2.0.0 |
| `docs/*` | Documentación actualizada |
