# MailSeguridad

**Versión:** 1.5.2  
**Stack:** Django 5.1 · Python 3 · SQLite  
**Repositorio:** [github.com/ferlogra/MailSeguridad](https://github.com/ferlogra/MailSeguridad)

---

## Descripción

Aplicación web Django para la **gestión de tickets de seguridad**. Permite consultar, filtrar y gestionar mensajes de tickets extraídos desde Office 365 mediante Microsoft Graph PowerShell, y asociarles actuaciones de seguimiento.

El proyecto consta de dos componentes:

| Componente | Descripción |
|------------|-------------|
| `get-Mail.ps1` | Script PowerShell que consulta la bandeja de entrada de Office 365, extrae IDs de tickets (INC/CS/CRQ/CVE/RT), agrupa por hilo y exporta a Excel y SQLite |
| **MailSeguridad** (Django) | Aplicación web para visualizar, filtrar y gestionar los mensajes y sus actuaciones asociadas |

---

## Requisitos

- Python 3.10+
- PowerShell 5.1+ (para el script de extracción)
- Módulos PowerShell: `Microsoft.Graph.Authentication`, `Microsoft.Graph.Mail`, `ImportExcel`, `PSSQLite`

### Dependencias Python

```
Django>=5.1
cryptography>=48.0
python-dateutil>=2.9
```

---

## Instalación rápida

```bash
# Clonar
git clone https://github.com/ferlogra/MailSeguridad.git
cd MailSeguridad

# Entorno virtual
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac

# Dependencias
pip install django cryptography python-dateutil

# Inicializar BD
python manage.py migrate

# Crear superusuario (opcional, para admin)
python manage.py createsuperuser

# Ejecutar
python manage.py runserver
```

Acceder a [http://localhost:8000](http://localhost:8000).

---

## Estructura del proyecto

```
MailSeguridad/
├── MailSeguridad/              # Configuración del proyecto Django
│   ├── settings.py             # Configuración general
│   ├── urls.py                 # Enrutamiento raíz
│   ├── version.py              # Versión semver (única fuente de verdad)
│   └── wsgi.py                 # Punto de entrada WSGI
├── seguridad/                  # Aplicación principal
│   ├── models.py               # Modelos de datos
│   ├── views.py                # Vistas (846+ líneas)
│   ├── forms.py                # Formularios
│   ├── admin.py                # Registro admin de Django
│   ├── table_manager.py        # Gestión de tablas (columnas, ordenación, paginación)
│   ├── urls.py                 # Rutas de mensajes
│   ├── urls_tipoactuaciones.py # Rutas de tipos de actuación
│   ├── urls_actuaciones.py     # Rutas de actuaciones
│   ├── urls_table_config.py    # Rutas de configuración de tablas
│   ├── user_urls.py            # Rutas de perfil de usuario
│   ├── templatetags/           # Template tags personalizados
│   │   └── seguridad_extras.py # dict_key, render_links, preserve_params
│   └── static/                 # Archivos estáticos
│       └── seguridad/
│           └── app.css         # Estilos de la aplicación
├── templates/                  # Plantillas Django
│   ├── base.html               # Plantilla base (navbar, modales, JS)
│   ├── menu.html               # Página principal con estadísticas
│   ├── registration/           # Plantillas de login
│   ├── seguridad/
│   │   ├── mensajes_list.html      # Lista de mensajes con filtros
│   │   ├── mensaje_detail.html     # Detalle de mensaje
│   │   ├── tipoactuaciones_list.html
│   │   ├── tipoactuacion_detail.html
│   │   ├── actuaciones_list.html
│   │   ├── actuacion_detail.html
│   │   ├── profile_form.html       # Perfil de usuario
│   │   ├── password_change_form.html  # Cambio de contraseña
│   │   ├── password_reset_*.html   # Restablecimiento de contraseña
│   │   ├── signup.html             # Registro
│   │   └── email_config.html       # Configuración SMTP
├── manage.py
└── README.md
```

---

## Modelos de datos

### Mensajes (no gestionado por Django — `managed = False`)

Tabla externa poblada por `get-Mail.ps1`. Solo lectura desde Django.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `Id` | `BIGINT PK` | Identificador interno |
| `Familia` | `TEXT` | Familia del ticket (ej. Red, Sistemas, Correo) |
| `ID_principal` | `TEXT` | Identificador del ticket (INC, CS, CRQ, CVE, RT…) |
| `Grupo` | `TEXT` | Grupo asignado |
| `Filtro` | `TEXT` | Criterio de filtrado |
| `Asunto_resumen` | `TEXT` | Resumen del asunto |
| `Estado` | `TEXT` | Estado actual del ticket |
| `Accion_tipo` | `TEXT` | Tipo de acción |
| `INC_relacionado` | `TEXT` | INC relacionado |
| `CS_relacionado` | `TEXT` | CS relacionado |
| `CRQ_asociado` | `TEXT` | CRQ asociado |
| `Ventana_o_fecha` | `TEXT` | Ventana de cambio/fecha prevista |
| `Ultimo_email_2026` | `TEXT` | Fecha del último email (ISO) |
| `Remitente_ultimo` | `TEXT` | Último remitente |
| `Num_Mensajes` | `INTEGER` | Número de mensajes en el hilo |
| `MessageIds` | `TEXT` | IDs de los mensajes (JSON) |
| `OutlookUrls` | `TEXT` | URLs de Outlook (con HYPERLINK) |
| `Revision` | `TEXT` | Número de revisión/iteración |
| `IdActuacion` | `INTEGER` | Contador de actuaciones asociadas |

### TipoActuaciones (gestionado por Django)

Catálogo de tipos de actuación.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `IdTipoActuacion` | `INTEGER PK` | Identificador |
| `Grupo` | `INTEGER` | Número de grupo (1, 2, 3…) |
| `Orden` | `INTEGER` | Orden dentro del grupo |
| `Breve` | `VARCHAR(256)` | Nombre corto del tipo |
| `Amplio` | `TEXT (8 KB)` | Descripción ampliada |
| `Cierra` | `BOOLEAN` | Indica si esta actuación cierra el ticket |

### Actuaciones (gestionado por Django)

Registro de actuaciones realizadas sobre los mensajes.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `IdActuacion` | `INTEGER PK` | Identificador |
| `IdTipoActuacion` | `FK → TipoActuaciones` | Tipo de actuación |
| `IdUser` | `FK → User (nullable)` | Usuario que registró la actuación |
| `FechaHora` | `DATETIME` | Fecha y hora (timezone-aware) |
| `Breve` | `VARCHAR(256)` | Descripción breve |
| `Amplio` | `TEXT (8 KB)` | Descripción ampliada |
| `Cierra` | `BOOLEAN` | Marca el mensaje como cerrado |
| `IdMensaje` | `FK → Mensajes (nullable)` | Mensaje al que pertenece |

### Usuarios (gestionado por Django)

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `username` | `VARCHAR(150)` | Nombre de usuario |
| `email` | `VARCHAR(254) UNIQUE` | Correo electrónico |
| `password` | `VARCHAR(128)` | Contraseña (hash) |
| `telefono` | `VARCHAR(32)` | Teléfono |
| `rol` | `VARCHAR(32)` | `administrador` o `usuario normal` |
| `fecha_alta` | `DATETIME` | Fecha de registro |
| `fecha_baja` | `DATETIME (nullable)` | Fecha de baja |

### Tablas auxiliares

- **`PasswordResetToken`** — Tokens de restablecimiento de contraseña (caducan a los 10 min)
- **`TableConfig`** — Configuraciones de columnas, orden y anchos guardadas por usuario

---

## URLs y vistas

### Públicas

| Ruta | Vista | Descripción |
|------|-------|-------------|
| `/` | `home_view` | Redirección a menú o login |
| `/login/` | `LoginView` (Django) | Inicio de sesión |
| `/registro/` | `signup_view` | Registro en dos pasos (verificación por email) |
| `/password_reset/` | `password_reset_request` | Solicitar restablecimiento de contraseña |
| `/password_reset/<token>/` | `password_reset_confirm` | Confirmar restablecimiento |
| `/__health__/` | `health_view` | Health check |

### Autenticadas

| Ruta | Vista | Descripción |
|------|-------|-------------|
| `/menu/` | `menu_view` | Menú principal con estadísticas |
| `/usuario/` | `profile_view` | Perfil de usuario |
| `/usuario/cambiar-contrasena/` | `password_change_view` | Cambiar contraseña |
| `/mensajes/` | `mensajes_list_view` | Lista de mensajes con filtros avanzados |
| `/mensajes/<pk>/` | `mensaje_detail_view` | Detalle/edición de mensaje |
| `/tipoactuaciones/` | `tipoactuaciones_list_view` | Lista de tipos de actuación |
| `/tipoactuaciones/nuevo/` | `tipoactuacion_create_view` | Crear tipo de actuación |
| `/tipoactuaciones/<pk>/` | `tipoactuacion_detail_view` | Detalle/edición de tipo |
| `/actuaciones/` | `actuaciones_list_view` | Lista de actuaciones |
| `/actuaciones/nuevo/` | `actuacion_create_view` | Crear actuación |
| `/actuaciones/<pk>/` | `actuacion_detail_view` | Detalle/edición de actuación |
| `/email-config/` | `email_config_view` | Configuración SMTP (admin) |

### API REST (JSON)

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/actuaciones/api/por-mensaje/<id>/` | `GET` | Lista actuaciones de un mensaje |
| `/actuaciones/api/crear/` | `POST` | Crear actuación |
| `/actuaciones/api/<pk>/eliminar/` | `POST` | Eliminar actuación |
| `/actuaciones/api/<pk>/actualizar/` | `POST` | Actualizar actuación |
| `/tipoactuaciones/api/lista/` | `GET` | Lista tipos para dropdowns |
| `/config-tabla/api/list/` | `GET` | Lista configuraciones de tabla |
| `/config-tabla/api/save/` | `POST` | Guardar configuración de tabla |

---

## Características

### Gestión de tablas (patrón miGTD)

Todas las listas (`mensajes`, `tipoactuaciones`, `actuaciones`) comparten:

- **Selector de columnas** — menú desplegable para mostrar/ocultar columnas
- **Reordenación por arrastre** — drag & drop para cambiar el orden de columnas
- **Redimensionamiento** — arrastrar borde de cabecera para ajustar ancho
- **Ordenación multicolumna** — Ctrl+click y Ctrl+Shift+click
- **Persistencia** — las configuraciones se guardan por usuario y se restauran al cargar

### Búsqueda avanzada de mensajes

- **Búsqueda libre** — por ID, asunto, familia, grupo, remitente o estado
- **Filtros por dropdown** — Familia, Grupo, Estado, Revisión (valores únicos extraídos de la BD)
- **Filtro por remitente** — búsqueda por texto parcial
- **Rango de fechas** — desde/hasta sobre `Ultimo_email`
- **Preservación de filtros** — se mantienen al paginar y ordenar

### Modal de actuaciones

Desde la lista de mensajes, el botón **Act.** abre un modal que permite:

- Ver actuaciones del mensaje
- **Crear** nuevas actuaciones con selección de tipo + breve + amplio
- **Editar** actuaciones existentes (formulario inline pre-rellenado)
- **Eliminar** múltiples actuaciones con selección por checkbox

### Renderizado de HYPERLINK

Las celdas que contienen fórmulas `=HYPERLINK(url, texto)` se renderizan automáticamente como enlaces HTML subrayados con cursor pointer.

### Autenticación y seguridad

- Registro con verificación por email (código de 8 dígitos)
- Restablecimiento de contraseña por email (token caduca a los 10 min)
- Cambio de contraseña desde el perfil (con verificación de la actual)
- Validadores de contraseña de Django (longitud, complejidad, no común)
- Roles: `administrador` y `usuario normal`
- Panel de administración Django en `/admin/`

### Configuración de email SMTP

Los administradores pueden configurar el servidor SMTP desde la interfaz web para el envío de correos de verificación y restablecimiento. Incluye prueba de envío.

---

## Script get-Mail.ps1

El script PowerShell `get-Mail.ps1` (`C:\ps1\get-Mail.ps1`) es el componente de extracción que:

1. Se conecta a Office 365 mediante Microsoft Graph
2. Consulta la bandeja de entrada (últimos 60 días por defecto)
3. Filtra correos según reglas configurables (remitente, asunto, cuerpo)
4. Extrae IDs de tickets: INC000000, CS000000, CRQ000000, CVE-YYYY-NNNN, RT-NNNNNN, SONATYPE
5. Agrupa correos por hilo (conversationId)
6. Exporta a Excel (con opción SQLite)

**Documentación completa:** [get-Mail.md](../get-Mail.md)

---

## Historial de versiones

| Tag | Fecha | Cambios |
|-----|-------|---------|
| v1.18.0 | 2026-06-20 | Limpieza de duplicados por headers + botón Compactar filas |
| v1.17.2 | 2026-06-18 | Modal dropdown con nombres de campo en AccAutoFields |
| v1.17.1 | 2026-06-18 | Fix import AccionesAuto en views |
| v1.17.0 | 2026-06-18 | CRUD AccionesAuto con inline AccAutoFields (1:N) |
| v1.16.0 | 2026-06-18 | Campo body renderizado al final a 2 columnas + refactor búsquedas |
| v1.15.2 | 2026-06-17 | Sesión documentada: refactors y mejoras UI |
| v1.15.1 | 2026-06-17 | Fix varios de UI/UX |
| v1.15.0 | 2026-06-17 | Mejoras en interfaz de tabla y búsqueda |
| v1.14.2 | 2026-06-17 | Fix paginación y filtros |
| v1.14.1 | 2026-06-17 | Fix ordenación multicolumna |
| v1.14.0 | 2026-06-17 | Ordenación multicolumna con Ctrl+click |
| v1.12.0 | 2026-06-17 | Configuraciones de tabla guardables por usuario |
| v1.11.1 | 2026-06-17 | Fix ancho de columnas redimensionables |
| v1.11.0 | 2026-06-17 | Columnas redimensionables con drag handle |
| v1.10.3 | 2026-06-17 | Fix selector de columnas |
| v1.10.2 | 2026-06-17 | Fix visibilidad de columnas |
| v1.10.1 | 2026-06-17 | Mejoras en col-selector drag & drop |
| v1.10.0 | 2026-06-16 | Columnas visibles configurables + drag reorder |
| v1.9.0 | 2026-06-16 | Vista detalle de mensaje con grid |
| v1.8.0 | 2026-06-16 | Paginación y búsqueda en listados |
| v1.7.0 | 2026-06-16 | Panel de administración + docs |
| v1.6.0 | 2026-06-16 | Dashboard con estadísticas |
| v1.5.2 | 2026-06-16 | Registro de modelos en admin de Django |
| v1.5.1 | 2026-06-16 | Botón editar actuación en modal (✏️) |
| v1.5.0 | 2026-06-16 | Búsqueda avanzada + cambio de contraseña |
| v1.3.1 | 2026-06-16 | Fix CSRF en modal de actuaciones |
| v1.3.0 | 2026-06-16 | Modal de actuaciones desde mensajes |
| v1.2.0 | 2026-06-16 | Tablas TipoActuaciones + Actuaciones |
| v1.1.0 | 2026-06-16 | Campo IdActuacion en mensajes |
| v1.0.0 | 2026-06-16 | Versión inicial |

---

## Licencia

Uso interno.
