# Pantallas (experiencia de usuario)

## Login

- URL: `/accounts/login/`
- Formulario: usuario y contraseña.
- Enlaces: "Registrarse" → `/registro/`, "¿Olvidaste tu contraseña?" → `/password_reset/`.
- Tras login exitoso, redirige a `/menu/`.

## Registro (dos pasos)

1. **Paso 1** (`/registro/`): formulario con nombre de usuario, email y contraseña (repetir). Validaciones: nombre de usuario único, email único, contraseña >= 8 caracteres, ambas contraseñas coinciden.
2. Al enviar, se genera un código de 8 dígitos y se envía al email registrado.
3. **Paso 2**: aparece un segundo formulario con el campo "Código de verificación" de 8 dígitos y un indicador del email al que se envió.
4. Al introducir el código correcto, se crea la cuenta, se inicia sesión automáticamente y se redirige al menú.

Si el usuario ya existe (username o email duplicados), se muestra el error en el paso 1.

## Restablecimiento de contraseña

1. **Solicitud** (`/password_reset/`): formulario con campo email. Si el email está registrado, se envía un enlace único con un token UUID.
2. **Confirmación** (`/password_reset/<token>/`): si el token es válido y no ha expirado (10 minutos por defecto), se muestra un formulario para introducir la nueva contraseña (dos campos).
3. Al enviar, se actualiza la contraseña y se redirige al login.
4. Si el token ha expirado o ya fue usado, se muestra una pantalla de error.

## Menú principal

- URL: `/menu/`
- Tarjetas con:
  - Total de mensajes en base de datos.
  - Familias disponibles con contador.
  - Revisiones pendientes con contador.
- Enlaces del menú lateral/principal:
  - **Mensajes** → listado de mensajes.
  - **Act. Tickets** → listado de mensajes con actuaciones.
  - **Actuaciones** → CRUD de actuaciones.
  - **Tipos de Actuación** → CRUD de catálogo.
  - **Docs** → visor de documentación.
  - **Perfil** → editar perfil de usuario.
  - **Configurar email** (solo administradores) → configuración SMTP.

## Mensajes (Tickets)

- URL: `/mensajes/`
- Tabla con las siguientes características:

### Barra de búsqueda y filtros
- **Búsqueda global** (`q`): texto libre que busca en 12 campos del mensaje (ID principal, asunto, familia, grupo, remitente, estado, revisión, destinatarios, CC, usuario, InternetMessageId, CS relacionado).
- **Filtros avanzados** (se combinan con AND):
  - Familia (desplegable con valores distintos de la BD)
  - Grupo (desplegable)
  - Remitente (texto, búsqueda parcial)
  - Estado (desplegable)
  - Revisión (desplegable)
  - Fecha desde / Fecha hasta (texto, formato AAAAMMDD o similar)
- **Filtro por campo** (`field` + `value`): cuando se accede desde un botón 🔍 del detalle de mensaje, la pantalla se abre pre-filtrada por el campo y valor seleccionados (p.ej. `?field=to&value=user@example.com`). El filtro es una whitelist de 5 campos: `to`, `internet_message_id`, `conversation_id`, `cs_relacionado`, `inc_relacionado`.

### Tabla de datos
- Columnas seleccionables: el usuario puede elegir qué columnas mostrar y en qué orden mediante un selector.
- **Columna de acción**: la primera columna tiene un botón "Detalle" que abre la vista de detalle individual.
- **Columna "Act."**: cada fila tiene un botón que abre un modal de actuaciones para gestionar las actuaciones de ese mensaje.
- Ordenación multi-columna:
  - **Clic** en cabecera: ordena ascendente; segundo clic: descendente; tercer clic: quita orden.
  - **Ctrl + clic**: añade columna al orden existente (ascendente).
  - **Shift + clic**: añade columna en orden descendente.
  - Un indicador numérico muestra el orden de prioridad de cada columna activa.
- Paginación: 50 registros por página.

### Selector de configuración
- Botón para guardar la configuración actual (columnas, orden, tamaño) con un nombre.
- La configuración llamada "default" se carga automáticamente al entrar.
- Lista desplegable para cambiar entre configuraciones guardadas.
- Botón para eliminar la configuración activa.

## Act. Tickets

- URL: `/actuaciones-tickets/`
- Misma interfaz que la pantalla de Mensajes, pero con columnas adicionales:
  - **Act. Tipo** — nombre corto del tipo de actuación.
  - **Act. Fecha** — fecha y hora de la actuación.
  - **Act. Breve** — descripción breve de la actuación.
  - **Cierra** — indica si la actuación cierra el ticket.
  - **Act. Usuario** — usuario que registró la actuación.
- Los mismos filtros de mensajes aplican aquí, y la búsqueda global también busca en los campos de actuación (breve, tipo y usuario).
- El JOIN entre Mensajes y Actuaciones se hace por `InternetMessageId`.

## Detalle de mensaje

- URL: `/mensajes/<pk>/`
- Muestra todos los campos del mensaje en un formulario desglosado en un grid de dos columnas.
- Campos editables: familia, ID principal, grupo, filtro, asunto resumen, estado, acción/tipo, INC/CS/CRQ relacionados, ventana/fecha, último email, remitente, num_mensajes, message_ids, outlook_urls, revisión, is_body_html, to, cc, user, headers, internet_message_id, conversation_id.
- **Campo "Cuerpo"**: se muestra al final ocupando las dos columnas completas (`grid-column: 1 / -1`) con un textarea de altura mínima 12rem.
- **Botones de búsqueda por campo (🔍)**: aparecen junto a los campos `to`, `internet_message_id`, `conversation_id`, `cs_relacionado` e `inc_relacionado`. Abren en una nueva pestaña la pantalla de Mensajes completa, pre-filtrada por ese campo y valor.
- Botones:
  - **Guardar** — persiste los cambios en la BD (el modelo Mensaje es managed=False pero permite escritura).
  - **Eliminar** — solo visible para administradores. Borra el registro.

## Actuaciones (modal)

- Accesible desde el botón "Act." de cada fila en las pantallas de Mensajes y Act. Tickets.
- Modal JavaScript que carga las actuaciones vía `actuaciones_por_mensaje_api` (GET).
- Listado de actuaciones existentes con: tipo, fecha, breve, amplio, cierra, usuario.
- Botón **Nueva actuación**: formulario dentro del modal para crear (vía `actuacion_create_api`).
- Botón **Editar** en cada actuación: formulario para modificar (vía `actuacion_update_api`).
- Botón **Eliminar** en cada actuación: confirmación y borrado (vía `actuacion_delete_api`).

## Actuaciones (página CRUD)

- **Listado** (`/actuaciones/`): tabla paginada con column-selector y búsqueda. Columnas: ID, Tipo, Usuario, Fecha/Hora, Breve, Amplio, Cierra.
- **Crear** (`/actuaciones/nuevo/`): formulario con selector de tipo de actuación (desplegable), fecha/hora, breve (requerido), amplio, cierra.
- **Detalle/Editar** (`/actuaciones/<pk>/`): mismo formulario que creación pero precargado. Incluye botón de eliminar.

## Tipos de Actuación

- **Listado** (`/tipoactuaciones/`): tabla paginada con column-selector y búsqueda. Columnas: ID, Grupo, Orden, Breve, Amplio, Cierra.
- **Crear** (`/tipoactuaciones/nuevo/`): formulario con grupo, orden, breve (requerido), amplio, cierra.
- **Detalle/Editar** (`/tipoactuaciones/<pk>/`): mismo formulario precargado. Incluye botón de eliminar.

## Documentación (Docs)

- URL: `/docs/`
- Visor de documentación markdown.
- Panel izquierdo: selector de archivos .md (escanea recursivamente desde la raíz del proyecto).
- Panel derecho: contenido renderizado como HTML (soporta bloques de código y tablas).
- Ideal para consultar documentación del proyecto sin salir de la aplicación.

## Perfil

- URL: `/usuario/`
- Formulario para editar: nombre de usuario, email, teléfono, fecha de baja, rol (solo administradores pueden cambiar el rol).
- Enlace a cambiar contraseña.

## Configuración de email

- URL: `/email-config/`
- Solo visible para usuarios administradores.
- Formulario con campos:
  - Servidor SMTP (host)
  - Puerto
  - Dirección de envío (from)
  - Usuario
  - Contraseña (no se muestra; si se deja vacía, se conserva la actual, cifrada con Fernet)
  - Tipo de cifrado: Sin cifrado / STARTTLS / SSL/TLS
- Botón **Guardar**: persiste la configuración en `config/email.json`.
- Botón **Enviar correo de prueba**: envía un email de prueba al destinatario indicado para verificar la configuración.
