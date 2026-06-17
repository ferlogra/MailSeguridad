# Arquitectura

## Stack tecnológico

| Componente | Versión |
|------------|---------|
| Python | 3.12 |
| Django | 5.1.6 |
| Base de datos | SQLite 3 |
| Frontend | HTML templates + CSS custom |
| Cifrado | cryptography (Fernet) |
| Motor de templates | Django Templates (Jinja-like) |

---

## Estructura de directorios

```
C:\ps1\MailSeguridad\
├── manage.py
├── README.md
├── config/
│   └── email.json              # Configuración SMTP cifrada con Fernet
├── templates/
│   ├── base.html               # Template base con CSS/JS comunes
│   ├── menu.html               # Pantalla de menú principal
│   ├── docs.html               # Visor de documentación
│   ├── registration/
│   │   └── login.html          # Login
│   └── seguridad/
│       ├── signup.html          # Registro en dos pasos
│       ├── profile_form.html    # Edición de perfil
│       ├── password_change_form.html
│       ├── password_reset_request.html
│       ├── password_reset_confirm.html
│       ├── password_reset_invalid.html
│       ├── email_config.html   # Configuración SMTP
│       ├── mensajes_list.html  # Listado de mensajes / act. tickets
│       ├── mensaje_detail.html # Detalle de mensaje
│       ├── actuaciones_list.html
│       ├── actuacion_detail.html
│       ├── tipoactuaciones_list.html
│       └── tipoactuacion_detail.html
├── MailSeguridad/              # Configuración del proyecto Django
│   ├── __init__.py
│   ├── settings.py             # Configuración general
│   ├── urls.py                 # Enrutador principal
│   ├── wsgi.py
│   ├── version.py              # Versión de la app (single source of truth)
│   └── mail_seguridad.db       # BD externa creada por get-Mail.ps1
├── seguridad/                  # Aplicación Django principal
│   ├── models.py               # Todos los modelos
│   ├── views.py                # Todas las vistas
│   ├── forms.py                # Formularios
│   ├── table_manager.py        # Gestión de tablas (column-selector, sort, config)
│   ├── email_config.py         # Configuración email cifrada con Fernet
│   ├── middleware.py           # CurrentUserMiddleware
│   ├── context_processors.py   # Variables globales en templates
│   ├── admin.py
│   ├── apps.py
│   ├── urls.py                 # Rutas de mensajes
│   ├── user_urls.py            # Rutas de perfil de usuario
│   ├── urls_actuaciones.py     # Rutas de actuaciones
│   ├── urls_tipoactuaciones.py # Rutas de tipos de actuación
│   ├── urls_table_config.py    # Rutas de configuración de tablas (API)
│   ├── templatetags/
│   │   ├── seguridad_extras.py # Filtros y tags personalizados
│   │       └── render_hyperlinks  # Reemplaza =HYPERLINK() por <a>
│   ├── migrations/
│   ├── management/
│   │   └── commands/
│   └── static/
│       └── css/
│           └── app.css         # Tema oscuro profesional con variables CSS
├── docs/                       # Documentación técnica
│   └── ...
└── media/                      # Archivos subidos (vacío por defecto)
```

---

## Base de datos dual

El proyecto utiliza dos bases de datos SQLite dentro del mismo archivo:

### `MailSeguridad/mail_seguridad.db` (base de datos `default`)
Contiene todas las tablas gestionadas por Django:
- `seguridad_user`
- `seguridad_passwordresettoken`
- `seguridad_tableconfig`
- `TipoActuaciones`
- `Actuaciones`
- Tablas del sistema Django (`auth_permission`, `django_session`, etc.)

### `Mensajes` (tabla externa dentro de la misma BD)
- La tabla `Mensajes` reside en la misma base de datos pero es creada y poblada por el script PowerShell `get-Mail.ps1`.
- El modelo `Mensaje` tiene `managed = False`, por lo que Django no intenta crearla ni modificarla.
- El campo `InternetMessageId` sirve como clave de unión textual con la tabla `Actuaciones` (campo `Mensaje`).

---

## table_manager.py

Sistema centralizado para gestionar tablas con columnas seleccionables, ordenación multi-columna y persistencia de configuraciones. Sigue el mismo patrón que el proyecto miGTD.

### Componentes

**TableRegistry**: diccionario tipado que almacena todas las configuraciones de tabla registradas. Las vistas se registran con `tables.register(TableView(...))`.

**TableView**: dataclass que describe una vista de tabla:
- `menu_option` — clave única (coincide con el nombre de la vista, ej. `mensajes_list`).
- `columns` — diccionario ordenado `{campo: etiqueta}` con TODAS las columnas disponibles.
- `sort_fields` — lista de campos ordenables.
- `sort_labels` — etiquetas para las cabeceras ordenables.
- `default_cols` — columnas visibles por defecto.
- `paginate_by` — registros por página (0 = sin paginación).
- `row_action_url_name` — nombre de la URL de detalle (genera botón por fila).

**Tablas registradas**:

| menu_option | Columnas | Paginación | URL acción |
|-------------|----------|------------|------------|
| `mensajes_list` | 25 columnas de Mensajes | 50 | `mensaje_detail` |
| `tipoactuaciones_list` | 6 columnas de TipoActuacion | 50 | `tipoactuacion_detail` |
| `actuaciones_list` | 7 columnas de Actuacion | 50 | `actuacion_detail` |
| `actuaciones_tickets` | 25 columnas de Mensajes + 5 de Actuaciones | 50 | `mensaje_detail` |

### Funciones públicas

- `build_table_context(request, user, cfg, base_query_string)` — construye el contexto de la tabla: información de ordenación, columnas ordenadas, configuración guardada, especificación de orden.
- `paginate_queryset(request, queryset, paginate_by)` — pagina cualquier queryset usando Django Paginator.
- `list_user_configs(user, menu_option)` — lista las configuraciones guardadas por el usuario para una vista.

### Ordenación multi-columna

El parámetro `?sort=campo1,-campo2` permite ordenación compuesta. Los signos `-` indican orden descendente. La función `_parse_sort` valida contra una whitelist de campos ordenables para evitar inyección.

### Modelo de datos asociado

Las configuraciones se persisten en el modelo `TableConfig` (ver [modelos.md](modelos.md)). Cada usuario puede tener múltiples configuraciones por vista, con `(usuario, menu_option, name)` como unique together. La configuración llamada `default` se carga automáticamente al entrar a la vista.

---

## Autenticación

### Modelo
- `User` extiende `AbstractUser`. Definido en `settings.AUTH_USER_MODEL`.
- Roles: `administrador` y `usuario normal`.

### Registro en dos pasos
1. El usuario rellena el formulario de registro con username, email y contraseña.
2. El sistema genera un código de 8 dígitos, lo almacena en sesión y lo envía por email.
3. El usuario introduce el código para verificar su email.
4. Al verificar, se crea el usuario con rol `usuario normal` y se inicia sesión automáticamente.

### Autenticación
- Login: vista genérica `LoginView` de Django con template propio.
- Logout: vista personalizada que llama a `logout()` y redirige.
- Decorador `@login_required` en todas las vistas que requieren sesión.

### Restablecimiento de contraseña
- Flujo completo con tokens UUID de un solo uso.
- `PasswordResetToken` con método `is_valid()` que comprueba uso y expiración.
- Timeout configurable vía `PASSWORD_RESET_TIMEOUT_MINUTES` (entorno o settings, por defecto 10 minutos).
- El enlace de reseteo se envía por email usando la configuración SMTP guardada.

---

## Configuración de email (Fernet)

### Almacenamiento
- Los ajustes SMTP se guardan en `config/email.json`, NO en la base de datos.
- La contraseña se cifra con Fernet usando una clave derivada de `SECRET_KEY`.

### Flujo
1. `EmailSettings.load()` — lee `config/email.json` y devuelve un dataclass con los valores.
2. `EmailSettings.save()` — serializa el dataclass a JSON y lo escribe.
3. `set_password(raw)` — cifra la contraseña con Fernet antes de guardarla.
4. `get_password()` — descifra la contraseña almacenada.

### Envío de email
- La función `_send_email_with_config` en `views.py` intenta usar la configuración guardada si está completa.
- Si no hay configuración, usa la configuración por defecto de Django (`EMAIL_BACKEND`, generalmente console backend).

---

## Relación Mensajes-Actuaciones

La relación entre `Mensaje` e `InternetMessageId` con `Actuacion.mensaje` es **textual**, no una foreign key real:

```
Mensajes.InternetMessageId ─── texto ─── Actuaciones.Mensaje
```

- La vista `actuaciones_tickets_view` realiza un `LEFT JOIN` explícito en SQL:
  ```sql
  LEFT JOIN Actuaciones a ON m.InternetMessageId = a.Mensaje
  ```
- El API `actuaciones_por_mensaje_api` filtra actuaciones por `mensaje_id` (que es el `InternetMessageId`).
- Esto permite que la tabla `Mensajes` siga siendo externa y no gestionada, sin dependencias de FK.

---

## URLs

Las rutas están organizadas en módulos separados para mantener la legibilidad:

```
MailSeguridad/urls.py (raíz)
├── /admin/                         → admin.site.urls
├── /login/, /accounts/login/       → LoginView
├── /logout/, /accounts/logout/     → logout_view
├── /registro/                      → signup_view
├── /password_reset/                → password_reset_request
├── /password_reset/<token>/        → password_reset_confirm
├── /email-config/                  → email_config_view
├── /usuario/                       → seguridad/user_urls.py
│   ├── /                           → profile_view
│   └── /cambiar-contrasena/        → password_change_view
├── /mensajes/                      → seguridad/urls.py
│   ├── /                           → mensajes_list_view
│   ├── /<pk>/                      → mensaje_detail_view
│   └── /borrar-todos/              → clear_mensajes_view
├── /tipoactuaciones/               → seguridad/urls_tipoactuaciones.py
│   ├── /                           → tipoactuaciones_list_view
│   ├── /nuevo/                     → tipoactuacion_create_view
│   ├── /<pk>/                      → tipoactuacion_detail_view
│   └── /api/lista/                 → tipoactuaciones_lista_api
├── /actuaciones/                   → seguridad/urls_actuaciones.py
│   ├── /                           → actuaciones_list_view
│   ├── /nuevo/                     → actuacion_create_view
│   ├── /<pk>/                      → actuacion_detail_view
│   ├── /api/por-mensaje/<id>/      → actuaciones_por_mensaje_api
│   ├── /api/crear/                 → actuacion_create_api
│   ├── /api/<pk>/eliminar/         → actuacion_delete_api
│   └── /api/<pk>/actualizar/       → actuacion_update_api
├── /actuaciones-tickets/           → actuaciones_tickets_view
├── /config-tabla/                  → seguridad/urls_table_config.py
│   ├── /list/                      → table_config_list_api
│   ├── /save/                      → table_config_save_api
│   └── /delete/                    → table_config_delete_api
├── /menu/                          → menu_view
├── /                               → home_view
├── /__health__/                    → health_view
└── /docs/                          → docs_view
```

---

## CSS

El tema visual se define en `seguridad/static/css/app.css`:
- Tema oscuro profesional con propiedades CSS personalizadas (variables).
- Sin dependencias de frameworks CSS externos (no Bootstrap, no Tailwind).
- Diseño responsive para las tablas y formularios.

---

## Middleware

### CurrentUserMiddleware
- Almacena el usuario actual en almacenamiento thread-local.
- Permite acceder al usuario desde cualquier parte del código (modelos, señales, etc.) mediante `get_current_user()`.
- Se limpia al finalizar cada petición.

---

## Context processors

### active_context
- Añade `app_version` a todas las plantillas, obtenido desde `MailSeguridad/version.py`.
