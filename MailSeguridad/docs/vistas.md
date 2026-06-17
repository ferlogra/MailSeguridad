# Vistas (views)

Todas las vistas están definidas en `seguridad/views.py`. Salvo `home_view` y `health_view`, las rutas que requieren autenticación usan el decorador `@login_required`.

---

## Autenticación

### `home_view`
- **Ruta**: `/`
- Redirige a `/menu/` si el usuario está autenticado, o a `/accounts/login/` en caso contrario.

### `health_view`
- **Ruta**: `/__health__/`
- Devuelve `"ok"` (útil para health checks).

### `menu_view`
- **Ruta**: `/menu/`
- Muestra el menú principal con estadísticas: total de mensajes, familias y revisiones disponibles.

### `login_view`
- Usa la vista genérica `LoginView` de Django con template `registration/login.html`.
- **Rutas**: `/login/` y `/accounts/login/`.

### `logout_view`
- **Ruta**: `/logout/` y `/accounts/logout/`
- Cierra la sesión y redirige a `accounts_login`.

---

## Registro en dos pasos

### `signup_view`
- **Ruta**: `/registro/`
- **Paso 1** — formulario `SignupForm`: usuario, email, contraseña. Al enviar, se genera un código de 8 dígitos y se almacena en `request.session['pending_signup']`. Se envía el código por email.
- **Paso 2** — formulario `VerificationForm`: código de 8 dígitos. Al validar, se crea el usuario con `rol = usuario normal` y se inicia sesión automáticamente.

---

## Restablecimiento de contraseña

### `password_reset_request_view`
- **Ruta**: `/password_reset/`
- Formulario `PasswordResetRequestForm` (solo email). Si el email existe, genera un UUID, crea un `PasswordResetToken` y envía un enlace de reseteo por email.

### `password_reset_confirm_view`
- **Ruta**: `/password_reset/<str:token>/`
- Verifica que el token sea válido (no usado, no expirado). Si es válido, muestra el formulario `PasswordResetForm` para introducir la nueva contraseña.

---

## Perfil de usuario

### `profile_view`
- **Ruta**: `/usuario/`
- Formulario `ProfileForm` (model form de `User`). Permite editar username, email, teléfono, fecha_baja y rol.

### `password_change_view`
- **Ruta**: `/usuario/cambiar-contrasena/`
- Formulario `CustomPasswordChangeForm`: requiere contraseña actual, nueva contraseña (con validación) y confirmación.

---

## Configuración de email

### `email_config_view`
- **Ruta**: `/email-config/`
- Solo accesible para administradores (`is_superuser` o `rol = administrador`).
- Formulario `EmailConfigForm` para configurar SMTP: host, puerto, from_email, usuario, contraseña (cifrada con Fernet), tipo de cifrado (none, STARTTLS, SSL/TLS).
- Incluye opción de enviar un correo de prueba.
- Los datos se guardan en `config/email.json` (fuera de la base de datos).

### `email_test_view`
- Integrada en `email_config_view` mediante el botón "Enviar correo de prueba".

---

## Listado de mensajes

### `mensajes_list_view`
- **Ruta**: `/mensajes/`
- Vista principal del sistema. Muestra la tabla de mensajes con:
  - **Búsqueda global** (`q`): busca en múltiples campos (id_principal, asunto_resumen, familia, grupo, remitente_ultimo, estado, revisión, to, cc, user, internet_message_id, cs_relacionado).
  - **Filtros avanzados**: familia, grupo, remitente, estado, revisión, fecha_desde, fecha_hasta. Los filtros avanzados se combinan con AND.
  - **Selectores de columna**: cada usuario puede seleccionar qué columnas mostrar y en qué orden.
  - **Ordenación multi-columna**: clic simple (asc/desc), Ctrl+clic añade columna de ordenación, Shift+clic añade en orden descendente.
  - **Paginación**: 50 registros por página.
  - **Guardar configuración**: las configuraciones se persisten en `TableConfig` con nombre "default" (carga automática) o nombres personalizados.
- Usa `table_manager.py` para construir el contexto de la tabla (`build_table_context`) y paginar (`paginate_queryset`).

### `actuaciones_tickets_view`
- **Ruta**: `/actuaciones-tickets/`
- Misma interfaz que `mensajes_list_view` pero con columnas añadidas de actuaciones (act_tipo, act_fecha, act_breve, act_cierra, act_user).
- Ejecuta SQL directo con `LEFT JOIN` entre `Mensajes` y `Actuaciones` (vía `InternetMessageId` = `Mensaje`), más `TipoActuaciones` y `seguridad_user`.
- Usa cursor raw de sqlite3 para evitar un bug de `CursorDebugWrapper` con `DEBUG=True`.
- Renderiza la misma plantilla `seguridad/mensajes_list.html` con `page_title = "Actuaciones"`.

---

## Detalle de mensaje

### `mensaje_detail_view`
- **Ruta**: `/mensajes/<int:pk>/`
- Muestra todos los campos editables de un mensaje individual.
- **POST con `_method=save`**: guarda los cambios en todos los campos editables.
- **POST con `_method=delete`**: elimina el mensaje (solo administradores).
- Renderiza `seguridad/mensaje_detail.html`.

### `clear_mensajes_view`
- **Ruta**: `/mensajes/borrar-todos/`
- POST exclusivo. Elimina **todos** los registros de la tabla Mensajes. Solo administradores.

### `detalle_api`
- No existe como endpoint separado. El detalle se obtiene mediante la respuesta JSON del endpoint `actuaciones_por_mensaje_api` para el modal de actuaciones.

---

## CRUD de tipo de actuaciones

### `tipoactuaciones_list_view`
- **Ruta**: `/tipoactuaciones/`
- Listado paginado de `TipoActuacion` con búsqueda, column-selector y ordenación multi-columna.

### `tipoactuacion_create_view`
- **Ruta**: `/tipoactuaciones/nuevo/`
- Formulario para crear un nuevo `TipoActuacion`. Campos: grupo, orden, breve, amplio, cierra.

### `tipoactuacion_detail_view`
- **Ruta**: `/tipoactuaciones/<int:pk>/`
- Vista/edición de un `TipoActuacion`. Incluye borrado vía `_method=delete`.

---

## CRUD de actuaciones

### `actuaciones_list_view`
- **Ruta**: `/actuaciones/`
- Listado paginado de `Actuacion` con `select_related` para evitar N+1 en tipo y usuario.

### `actuacion_create_view`
- **Ruta**: `/actuaciones/nuevo/`
- Formulario para crear una nueva `Actuacion`. Permite seleccionar tipo de actuación de un desplegable.

### `actuacion_detail_view`
- **Ruta**: `/actuaciones/<int:pk>/`
- Vista/edición de una `Actuacion` individual. Incluye borrado vía `_method=delete`.

---

## Vistas de documentación

### `docs_view`
- **Ruta**: `/docs/`
- Visor de documentación markdown. Escanea recursivamente archivos `.md` desde `C:\ps1\` (BASE_DIR.parent).
- Muestra un selector de archivos y renderiza el contenido markdown a HTML usando la librería `markdown` con extensiones `fenced_code` y `tables`.

---

## APIs JSON

### `tipoactuaciones_list_api`
- **Ruta**: `/tipoactuaciones/api/lista/`
- GET. Devuelve JSON con todos los `TipoActuacion` ordenados por grupo, orden.
- Cada registro: `{ id, grupo, orden, breve }`.

### `actuaciones_por_mensaje_api`
- **Ruta**: `/actuaciones/api/por-mensaje/<str:mensaje_id>/`
- GET. Devuelve JSON con todas las actuaciones asociadas a un `InternetMessageId`.
- Cada registro: `{ id_actuacion, id_tipo_actuacion, tipo_breve, fecha_hora, breve, amplio, cierra, username }`.

### `actuacion_create_api`
- **Ruta**: `/actuaciones/api/crear/`
- POST (JSON). Crea una actuación. Campos: `id_tipo_actuacion`, `breve`, `amplio`, `cierra`, `mensaje`.
- Devuelve `{ status, id }`.

### `actuacion_update_api`
- **Ruta**: `/actuaciones/api/<int:pk>/actualizar/`
- POST (JSON). Actualiza una actuación. Campos: `id_tipo_actuacion`, `fecha_hora`, `breve`, `amplio`, `cierra`.
- Devuelve `{ status, id }`.

### `actuacion_delete_api`
- **Ruta**: `/actuaciones/api/<int:pk>/eliminar/`
- POST. Elimina una actuación. Devuelve `{ status }`.

### `table_config_list_api`
- **Ruta**: `/config-tabla/list/`
- GET. Parámetro: `menu_option`. Devuelve JSON con todas las configuraciones guardadas del usuario para esa vista.

### `table_config_save_api`
- **Ruta**: `/config-tabla/save/`
- POST (JSON). Guarda o actualiza una configuración de tabla. Campos: `menu_option`, `name`, `selected_fields`, `sort_order`, `size_columns`.
- Usa `update_or_create` con unique `(usuario, menu_option, name)`.

### `table_config_delete_api`
- **Ruta**: `/config-tabla/delete/`
- POST (JSON). Elimina una configuración de tabla por `id`.
