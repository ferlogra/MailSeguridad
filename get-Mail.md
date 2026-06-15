# get-Mail.ps1

**Versión actual:** 1.7  
**Última actualización:** 2026-06-16  
**Requiere:** PowerShell 5.1+

---

## Descripción

Script que consulta la bandeja de entrada de Office 365 mediante Microsoft Graph PowerShell, aplica filtros configurables por remitente/asunto/cuerpo, extrae IDs de tickets (INC/CS/CRQ/CVE/SONATYPE/RT), agrupa los correos por hilo, detecta estados y relaciones, y exporta el resultado a Excel (con opción de exportar también a SQLite).

No descarga correos ni adjuntos; solo consulta metadatos y contenido textual necesario para el análisis.

---

## Dependencias

El script verifica e instala automáticamente los siguientes módulos desde PowerShell Gallery (si se usa `-InstallDependencies`):

| Módulo | Versión mínima | Propósito |
|--------|---------------|-----------|
| `Microsoft.Graph.Authentication` | — | Autenticación contra Microsoft Graph |
| `Microsoft.Graph.Mail` | — | Lectura de correos del buzón |
| `ImportExcel` | — | Exportación a Excel sin Excel instalado |
| `PSSQLite` (v1.5+) | — | Exportación a SQLite |

---

## Parámetros

### `-UserId`
UPN o identificador del buzón a consultar.  
Ejemplo: `fernando.lopez@tirea.es`  
Si no se indica, se obtiene automáticamente del contexto de Graph.

### `-DaysBack`
Número de días hacia atrás a consultar.  
Por defecto: `60`. Rango válido: `1` – `3650`.

### `-MailFolderName`
Nombre de la carpeta de correo a consultar.  
Por defecto: `"Bandeja de entrada"`.  
Soporta subcarpetas mediante búsqueda recursiva.

### `-MailFolderNameMove`
Nombre de la subcarpeta destino donde mover los correos filtrados.  
Por defecto: `""` (no mueve correos).  
Requiere que la subcarpeta exista dentro de `MailFolderName`.

### `-TemplatePath`
Ruta a la plantilla Excel `.xlsx`.  
Por defecto: `C:\ps1\tickets_telefonica.xlsx`.  
Si no existe, se crea un libro nuevo con la estructura de columnas.

### `-WorksheetName`
Nombre de la hoja del Excel de salida.  
Por defecto: `"Tickets"`.

### `-OutputPath`
Ruta del Excel de salida.  
Por defecto: `C:\ps1\`.  
El nombre del archivo se genera como `tickets_telefonica_AAAAMMDD_HHmmss.xlsx`.

### `-InstallDependencies`
Si se indica, instala automáticamente los módulos faltantes desde PowerShell Gallery.

### `-Scope`
Ámbito de instalación de módulos.  
Valores: `CurrentUser` (por defecto), `AllUsers`.

### `-ForceRecreateOutput`
Si se indica y ya existe el archivo de salida, lo sobrescribe.

### `-VerboseLogging`
Muestra mensajes de depuración (`DEBUG`) en pantalla.

### `-MaxMessages`
Límite máximo de mensajes a leer desde la carpeta.  
Por defecto: `2000`. Rango válido: `1` – `50000`.  
Útil para controlar duración/coste de la consulta.

### `-UseGraphWebLinkOnly`
Si se indica, solo utiliza la propiedad `webLink` devuelta por Graph para el enlace a Outlook.  
Si no se indica, cuando `webLink` venga vacío se construye un deeplink OWA de compatibilidad.

### `-outBBDD` (v1.5+)
Ruta a la base de datos SQLite donde exportar los mensajes filtrados.  
Si se indica, los mensajes se guardan en la tabla `Mensajes` de la BBDD especificada, con los mismos campos que la salida Excel.  
Ejemplo: `-outBBDD "C:\Datos\tickets.db"`  
Si la BBDD no existe, se crea junto con la tabla. Si ya existe, los nuevos registros se añaden a la tabla existente (modo acumulativo).

---

## Columnas de salida (Excel y SQLite)

| Columna | Descripción |
|---------|-------------|
| `Familia` | Familia del ID principal (INC, CS, CRQ, CVE, RT, etc.) |
| `ID_principal` | ID principal extraído del asunto/cuerpo |
| `Grupo` | Grupo del filtro que clasificó el mensaje |
| `Filtro` | Nombre del filtro que clasificó el mensaje |
| `Asunto_resumen` | Asunto del último mensaje, sin prefijos RE/RV/FW/FWD |
| `Estado` | Estado detectado del hilo (resuelto, pendiente, en proceso) |
| `Accion_tipo` | Tipo de acción identificada (Backup, Seguridad/red, Snapshot, etc.) |
| `INC_relacionado` | IDs INC relacionados en el hilo |
| `CS_relacionado` | IDs CS relacionados en el hilo |
| `CRQ_asociado` | IDs CRQ asociados en el hilo |
| `Ventana_o_fecha` | Ventana de mantenimiento o fecha extraída |
| `Ultimo_email_2026` | Fecha/hora del último correo en el hilo |
| `Remitente_ultimo` | Remitente del último correo |
| `Num_Mensajes` | Número de mensajes en el hilo |
| `MessageIds` | Lista de IDs de mensaje del hilo |
| `OutlookUrls` | Lista de URLs a los mensajes en Outlook |
| `Revision` (v1.5+) | Timestamp de la ejecución (formato `AAAAMMDD-HHmmss`) |
| `IdActuacion` (v1.7+) | ID de actuación (entero, editable desde la web, por defecto 0) |

---

## Ejemplos

### Exportación básica a Excel
```powershell
.\get-Mail.ps1 -UserId "fernando.lopez@tirea.es" -InstallDependencies -VerboseLogging
```

### Exportación a Excel + SQLite
```powershell
.\get-Mail.ps1 -UserId "fernando.lopez@tirea.es" -outBBDD "C:\Datos\tickets" -InstallDependencies
```
Genera `C:\Datos\tickets.db` con la tabla `Mensajes` poblada.

### Rango de fechas personalizado con salida en ruta concreta
```powershell
.\get-Mail.ps1 `
    -UserId "fernando.lopez@tirea.es" `
    -DaysBack 45 `
    -TemplatePath "C:\Informes\tickets_telefonica.xlsx" `
    -OutputPath "C:\Informes\tickets_telefonica_$(Get-Date -Format yyyyMMdd).xlsx" `
    -InstallDependencies `
    -ForceRecreateOutput
```

### Mover correos filtrados a subcarpeta
```powershell
.\get-Mail.ps1 -UserId "fernando.lopez@tirea.es" -MailFolderNameMove "Procesados" -InstallDependencies
```

---

## Filtros configurables

Los filtros están definidos en el array `$Filters` dentro del script. Cada filtro soporta:

| Propiedad | Valores |
|-----------|---------|
| `Mode` | `Include` (solo estos), `Exclude` (descartar estos) |
| `Logic` | `AND` (todas las condiciones), `OR` (cualquier condición) |
| `Grupo` | Etiqueta de clasificación (Telefonica, CrowdStrike, RT, etc.) |
| `Conditions` | Array de condiciones con `Field`, `Type` y `Value` |

### Campos de condición (`Field`)
- `From` — Dirección del remitente
- `Domain` — Dominio del remitente (extraído automáticamente)
- `Subject` — Asunto del correo
- `Body` — Cuerpo del correo
- `Folder` — Carpeta donde se encuentra

### Operadores de condición (`Type`)
- `Contains` / `NotContains`
- `Equals` / `NotEquals`
- `Regex` / `NotRegex`

### Filtros incluidos por defecto

| Filtro | Grupo | Remitente | Condición adicional |
|--------|-------|-----------|---------------------|
| Intel sin patrón Filtraciones | Smarthc | intel@smarthc.es | Asunto: `Filtraciones dd/dd/dddd` |
| Nexus Policy Alert | NexusIQServer | nexusiqserver@tirea.es | Asunto contiene `Policy Alert` |
| Imperva Attack Report | Imperva | no_reply@out.imperva.com | Asunto contiene `Attack Report is Ready` |
| Aiuken Case# | Aiuken | support@aiuken.com | Asunto contiene `Case #` |
| Aiuken Ticket# | Aiuken | support@aiuken.com | Asunto contiene `Ticket#` |
| operacionescloud CRQ | Telefonica | operacionescloudms.tcct@telefonica.com | Asunto contiene `CRQ` |
| Tickets RT | RT | `.rt@tirea.es` | Asunto con patrón `[Servicio #num]` |
| Alarmas CrowdStrike | CrowdStrike | falcon@crowdstrike.com | Asunto contiene `New detection` |
| Alerta SOAR | Telefonica | no-reply-soar@... | Asunto contiene `INC000` |
| Identidad/Autorización | Telefonica | itsmtelefonicatech@service-now.com | Asunto contiene `Case CS00` |
| Soporte Telefónica | Telefonica | @telefonica.com / argonauta... | Asunto contiene `INC00` |
| Soporte Telefónica2 | Telefonica | servicedesk.tcct@... | Asunto contiene `CS00` |
| Tirea | Telefonica | @tirea.es | Asunto contiene `CS00`/`INC00`/`CRQ00` |

---

## Changelog

### v1.7 (2026-06-16)
**Aportaciones:**

#### Nuevos campos
- ✨ Nuevo campo `IdActuacion` (INTEGER NOT NULL DEFAULT 0) en la tabla `Mensajes` de SQLite. Añadido al CREATE TABLE, al INSERT y mediante ALTER TABLE a bases de datos existentes.
- ✨ El campo `IdActuacion` se muestra y edita desde la web app MailSeguridad v1.1.0 (columna en tabla + campo editable en detalle).

---

### v1.6 (2026-06-16)
**Aportaciones:**

#### Mejoras en visualización
- ✨ Renderizado de `=HYPERLINK(url,texto)` como enlace HTML: los campos con este formato se muestran subrayados, con cursor pointer y color azul. Al hacer clic se abre la URL en una nueva pestaña.
- 🐛 **Bug visual**: El campo `ID Principal` en la tabla mostraba el texto completo de la fórmula en lugar del enlace renderizado. Corregido aplicando el filtro `render_links` a la rama específica de `id_principal`.

#### Integración con MailSeguridad (Django Web App)
- ✨ Aplicación Django `MailSeguridad` creada para gestionar la base de datos SQLite generada por `get-Mail.ps1 -outBBDD`.
- ✨ Gestión completa de columnas: selector con drag-and-drop, visibilidad, guardar/cargar/borrar configs, y redimensionado por arrastre (patrón miGTD).
- ✨ Vista detalle de mensajes: edición en formulario 2-columnas, borrado con doble confirmación (solo admin).
- ✨ Autenticación: registro en 2 pasos (verificación por email), login, reset de contraseña por email.
- ✨ Exportación a SQLite desde PowerShell con modo append (no borra datos previos).

---

### v1.5 (2026-06-15)
**Aportaciones:**

#### Nuevas funcionalidades
- ✨ Nuevo parámetro `-outBBDD`: exporta los mensajes filtrados a una base de datos SQLite (tabla `Mensajes`) con los mismos campos que la salida Excel.
- ✨ Nueva función `Export-ResultSqlite`: crea la tabla `Mensajes` si no existe e inserta los registros en modo acumulativo (no borra datos previos).
- ✨ Nueva dependencia: módulo `PSSQLite` para la conexión con SQLite.
- ✨ Campo `Revision` añadido al objeto normalizado de cada mensaje, con timestamp de la ejecución (`AAAAMMDD-HHmmss`). Se refleja tanto en Excel como en SQLite.

#### Correcciones de bugs
- 🐛 **Bug -Contains → -like** en `Get-ActionType`: `$Messages[0].From -Contains ".rt@tirea.es"` no funcionaba porque `-Contains` es para colecciones, no para substrings. Corregido a `-like "*.rt@tirea.es"`.
- 🐛 **Bug -contains → .Contains()** en `Build-OutputRows`: `$latest.FromName -contains '@'` siempre daba `$false` por la misma razón. Corregido a `.Contains('@')`.
- 🐛 **Bug sintaxis ${}** en log: `${$Mail2.From}` no expandía la expresión correctamente. Corregido a `$($Mail2.From)`.
- 🐛 **Typo CVEE* → CVE*** en `Get-RelatedIds`: el patrón `"CVEE*"` impedía relacionar IDs CVE. Corregido a `"CVE*"`.
- 🐛 **Función duplicada** `Resolve-MailFolderId` definida dos veces. Eliminada la segunda definición.

#### Mejoras internas
- 🧹 Código muerto eliminado: la función duplicada `Resolve-MailFolderId`.
- 📝 Actualizada la ayuda del script con el nuevo parámetro y ejemplo de uso con `-outBBDD`.
- 📄 Este fichero de documentación `get-Mail.md` creado.

---

### v1.4 (Anterior)
- Funcionalidad completa de filtrado Include/Exclude con lógica AND/OR.
- Extracción de IDs (INC, CS, CRQ, CVE, sonatype, RT) por regex.
- Detección de estado de hilos (abierto/resuelto/en proceso).
- Detección de tipo de acción (Backup, Seguridad, SOAR, etc.).
- Exportación a Excel con plantilla.
- Movimiento de correos a subcarpeta destino.
- Deeplink OWA de compatibilidad cuando `webLink` está vacío.
- Búsqueda recursiva de subcarpetas.
- Instalación automática de dependencias (`-InstallDependencies`).

---

### v1.0 – v1.3 (Histórico)
- Migración de Outlook COM a Microsoft Graph PowerShell.
- Implementación del sistema de filtros configurables.
- Agrupación por ID principal y detección de relaciones entre tickets.
- Soporte para mensajes SOAR.
- Parámetros de personalización (DaysBack, MaxMessages, etc.).
- Logging con niveles INFO/WARN/ERROR/DEBUG.

---

## Notas

- **Permisos Graph requeridos**: `Mail.Read`, `Mail.ReadBasic`, `User.Read`, `Mail.ReadWrite` (este último necesario para mover correos a otra carpeta).
- La exportación a Excel usa el módulo `ImportExcel` y **no requiere** tener Microsoft Excel instalado.
- La exportación a SQLite usa el módulo `PSSQLite` con `System.Data.SQLite` como proveedor subyacente.
- Los filtros se definen directamente en el array `$Filters` del script. Para personalizarlos, editar el archivo `.ps1`.
- El comportamiento por defecto es **whitelist**: solo se incluyen correos que matcheen alguna regla `Include` explícita. Mensajes de remitentes no contemplados son ignorados.
