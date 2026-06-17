# Modelos de datos

## User

Modelo de usuario basado en `AbstractUser` de Django. Añade campos específicos de la aplicación para rol, teléfono y fechas de alta/baja.

| Campo | Tipo SQL | Descripción |
|-------|----------|-------------|
| `id` | `integer` (PK auto) | Identificador único |
| `password` | `varchar(128)` | Hash de contraseña |
| `last_login` | `datetime` | Último inicio de sesión |
| `is_superuser` | `bool` | Acceso al panel admin de Django |
| `username` | `varchar(150)` | Nombre de usuario (único) |
| `first_name` | `varchar(150)` | Nombre (heredado de AbstractUser) |
| `last_name` | `varchar(150)` | Apellidos (heredado de AbstractUser) |
| `email` | `varchar(254)` | Correo electrónico (unique=True) |
| `is_staff` | `bool` | Acceso al panel admin de Django |
| `is_active` | `bool` | Cuenta activa |
| `date_joined` | `datetime` | Fecha de registro |
| `telefono` | `varchar(32)` | Teléfono de contacto |
| `fecha_alta` | `datetime` | Fecha de alta (auto_now_add) |
| `fecha_baja` | `datetime` | Fecha de baja (nullable) |
| `rol` | `varchar(32)` | Rol del usuario: `administrador` o `usuario normal` |

La tabla se llama `seguridad_user`. El modelo `AUTH_USER_MODEL` en settings.py apunta a `seguridad.User`.

---

## PasswordResetToken

Token de un solo uso para el restablecimiento de contraseña.

| Campo | Tipo SQL | Descripción |
|-------|----------|-------------|
| `id` | `integer` (PK auto) | Identificador único |
| `token` | `varchar(36)` | UUID único del token |
| `usuario_id` | `integer` (FK) | Relación con `seguridad_user.id` |
| `created_at` | `datetime` | Fecha de creación (auto_now_add) |
| `used` | `bool` | Marca si ya fue usado |

Métodos:
- `is_expired()` — comprueba si han pasado más de `PASSWORD_RESET_TIMEOUT_MINUTES` minutos (por defecto 10).
- `is_valid()` — devuelve `True` si no está usado y no ha expirado.

Al usarse, el token se elimina de la base de datos.

---

## TableConfig

Configuración persistente de columnas, orden y tamaño para las tablas del interfaz.

| Campo | Tipo SQL | Descripción |
|-------|----------|-------------|
| `id` | `integer` (PK auto) | Identificador único |
| `usuario_id` | `integer` (FK) | Relación con `seguridad_user.id` |
| `menu_option` | `varchar(64)` | Identificador de la vista (`mensajes_list`, `tipoactuaciones_list`, etc.) |
| `name` | `varchar(64)` | Nombre de la configuración (`default` se carga automáticamente) |
| `selected_fields` | `text` (JSON) | Lista ordenada de columnas visibles |
| `sort_order` | `text` (JSON, nullable) | Criterios de ordenación, ej: `["-received", "family"]` |
| `size_columns` | `text` (JSON, nullable) | Anchos en píxeles por columna |

Restricción `unique_together`: `(usuario, menu_option, name)` — un usuario no puede tener dos configuraciones con el mismo nombre para la misma vista.

---

## Mensaje

Modelo **no gestionado por Django** (`managed = False`) que se mapea a la tabla externa `Mensajes` de la base de datos `mail_seguridad.db`. Esta tabla es creada y poblada por el script PowerShell `get-Mail.ps1`.

| Columna SQL | Campo Python | Tipo | Descripción |
|------------|--------------|------|-------------|
| `Id` | `id` | `BigAutoField` (PK) | Identificador único |
| `Familia` | `familia` | `text` (nullable) | Familia o categoría del mensaje |
| `ID_principal` | `id_principal` | `text` (nullable) | Identificador principal (ej. INC, CS, CRQ) |
| `Grupo` | `grupo` | `text` (nullable) | Grupo |
| `Filtro` | `filtro` | `text` (nullable) | Filtro de búsqueda |
| `Asunto_resumen` | `asunto_resumen` | `text` (nullable) | Resumen del asunto |
| `Estado` | `estado` | `text` (nullable) | Estado del mensaje |
| `Accion_tipo` | `accion_tipo` | `text` (nullable) | Acción / Tipo |
| `INC_relacionado` | `inc_relacionado` | `text` (nullable) | INC relacionado |
| `CS_relacionado` | `cs_relacionado` | `text` (nullable) | CS relacionado |
| `CRQ_asociado` | `crq_asociado` | `text` (nullable) | CRQ asociado |
| `Ventana_o_fecha` | `ventana_o_fecha` | `text` (nullable) | Ventana o fecha |
| `Ultimo_email_2026` | `ultimo_email` | `text` (nullable) | Fecha del último email |
| `Remitente_ultimo` | `remitente_ultimo` | `text` (nullable) | Remitente del último email |
| `Num_Mensajes` | `num_mensajes` | `integer` (nullable) | Número de mensajes |
| `MessageIds` | `message_ids` | `text` (nullable) | IDs de mensaje (separados por comas) |
| `OutlookUrls` | `outlook_urls` | `text` (nullable) | URLs de Outlook |
| `Revision` | `revision` | `text` (nullable) | Marca de revisión (AAAAMMDD-HHmmss) |
| `Body` | `body` | `text` (nullable) | Cuerpo del mensaje |
| `IsBodyHTML` | `is_body_html` | `bool` (nullable) | Indica si el Body está en HTML |
| `To` | `to` | `text` (nullable) | Destinatarios |
| `Cc` | `cc` | `text` (nullable) | Con copia |
| `InternetMessageHeaders` | `internet_message_headers` | `text` (nullable) | Cabeceras completas del mensaje |
| `InternetMessageId` | `internet_message_id` | `text` (nullable) | ID único del mensaje (Internet Message ID) |
| `ConversationId` | `conversation_id` | `text` (nullable) | ID de la conversación |
| `User` | `user` | `text` (nullable) | Usuario asociado |

**Nota importante**: `Mensaje` es un modelo de solo lectura desde la perspectiva de Django. La tabla es externa y su ciclo de vida lo gestiona `get-Mail.ps1`. El modelo existe únicamente para que Django pueda consultar los datos mediante el ORM.

---

## TipoActuacion

Catálogo de tipos de actuación. Tabla gestionada: `TipoActuaciones`.

| Columna SQL | Campo Python | Tipo | Descripción |
|------------|--------------|------|-------------|
| `IdTipoActuacion` | `id_tipo_actuacion` | `AutoField` (PK) | Identificador único |
| `Grupo` | `grupo` | `integer` | Número de grupo (para agrupar tipos) |
| `Orden` | `orden` | `smallint` | Orden dentro del grupo |
| `Breve` | `breve` | `varchar(256)` | Nombre corto del tipo de actuación |
| `Amplio` | `amplio` | `text(8192)` | Descripción amplia (opcional) |
| `Cierra` | `cierra` | `bool` | Indica si esta actuación cierra el ticket |

Ordenación por defecto: `grupo`, `orden`.

---

## Actuacion

Registro de actuaciones realizadas sobre mensajes. Tabla gestionada: `Actuaciones`.

| Columna SQL | Campo Python | Tipo | Descripción |
|------------|--------------|------|-------------|
| `IdActuacion` | `id_actuacion` | `AutoField` (PK) | Identificador único |
| `IdTipoActuacion` | `id_tipo_actuacion` | `integer` (FK) | Relación con `TipoActuaciones.IdTipoActuacion` (on_delete=PROTECT) |
| `IdUser` | `id_user` | `integer` (FK) | Relación con `seguridad_user.id` (on_delete=SET_NULL) |
| `FechaHora` | `fecha_hora` | `datetime` | Fecha y hora de la actuación |
| `Breve` | `breve` | `varchar(256)` | Descripción breve |
| `Amplio` | `amplio` | `text(8192)` | Descripción amplia (opcional) |
| `Cierra` | `cierra` | `bool` | Indica si cierra el ticket |
| `Mensaje` | `mensaje` | `text` (nullable) | ID del mensaje asociado (InternetMessageId) |

La relación con `Mensaje` no es una foreign key real de base de datos, sino un vínculo **textual** mediante el campo `InternetMessageId`. La vista `actuaciones_tickets_view` realiza un `LEFT JOIN` entre `Mensajes.InternetMessageId` y `Actuaciones.Mensaje`.

---

---

## AccionesAuto

Configuración de acciones automáticas para aplicar a mensajes o a otras acciones. Tabla gestionada: `AccionesAuto`.

| Columna SQL | Campo Python | Tipo | Descripción |
|------------|--------------|------|-------------|
| `IDAccAuto` | `IDAccAuto` | `AutoField` (PK) | Identificador único |
| `DescAccAuto` | `DescAccAuto` | `varchar(64)` | Descripción de la acción automática |
| `Tipo` | `Tipo` | `varchar(16)` | Tipo: `Mensaje` (aplica a mensajes) o `Accion` (aplica a acciones) |
| `Hijo` | `Hijo` | `integer` (FK, nullable) | Auto-referencia: `IDAccAuto` del registro hijo asociado (on_delete=SET_NULL) |

---

## AccAutoFields

Condiciones de campo para una acción automática. Relación 1:N con `AccionesAuto`. Tabla gestionada: `AccAutoFields`.

| Columna SQL | Campo Python | Tipo | Descripción |
|------------|--------------|------|-------------|
| `IDAaccAutoField` | `IDAaccAutoField` | `AutoField` (PK) | Identificador único |
| `IDAccAuto` | `IDAccAuto` | `integer` (FK) | Relación con `AccionesAuto.IDAccAuto` (on_delete=CASCADE) |
| `Orden` | `Orden` | `integer` | Orden de evaluación de la condición |
| `Field` | `Field` | `varchar(128)` | Nombre del campo a evaluar |
| `Cond` | `Cond` | `varchar(16)` | Operador de comparación (ver valores abajo) |
| `Valor` | `Valor` | `varchar(256)` | Valor contra el que comparar |

**Valores de `Cond`** (operadores similares a Python):

| Código | Significado |
|--------|-------------|
| `EQ` | Igual a (`==`) |
| `NE` | No igual a (`!=`) |
| `GT` | Mayor que (`>`) |
| `GE` | Mayor o igual a (`>=`) |
| `LT` | Menor que (`<`) |
| `LE` | Menor o igual a (`<=`) |
| `Contains` | Contiene (`in`) |
| `NContains` | No contiene (`not in`) |
| `Like` | Es como (coincidencia de patrón) |
| `NLike` | No es como |
| `Find` | Aparece (búsqueda de substring) |
| `NFind` | No aparece |

Ordenación por defecto: `IDAccAuto`, `Orden`.

---

## Resumen de tablas

| Tabla SQL | Modelo | Gestionada | Propósito |
|-----------|--------|------------|-----------|
| `seguridad_user` | `User` | Sí | Usuarios y autenticación |
| `seguridad_passwordresettoken` | `PasswordResetToken` | Sí | Tokens de reseteo de contraseña |
| `seguridad_tableconfig` | `TableConfig` | Sí | Configuraciones de tabla |
| `Mensajes` | `Mensaje` | No (externa) | Datos importados por `get-Mail.ps1` |
| `TipoActuaciones` | `TipoActuacion` | Sí | Catálogo de tipos de actuación |
| `Actuaciones` | `Actuacion` | Sí | Registro de actuaciones |
| `AccionesAuto` | `AccionesAuto` | Sí | Configuración de acciones automáticas |
| `AccAutoFields` | `AccAutoFields` | Sí | Condiciones de campo para acciones automáticas |
