# Microsoft.Graph.Mail — Documentación Completa

> Fecha de elaboración: 17/06/2026
> Basado en documentación oficial de Microsoft Learn, PowerShell Gallery, y artículos técnicos de WOSHUB, M365 Corner, C7Solutions, y Mike Hacker.

---

## 1. Introducción al Módulo Microsoft.Graph.Mail

El módulo `Microsoft.Graph.Mail` forma parte del SDK de PowerShell para Microsoft Graph en su versión 1.0. Proporciona un conjunto completo de cmdlets para interactuar con el correo electrónico de Exchange Online a través de la API de Outlook Mail de Microsoft Graph.

### 1.1. ¿Qué permite hacer?

- Leer, crear, actualizar y eliminar mensajes de correo electrónico
- Gestionar carpetas y subcarpetas del buzón
- Enviar, reenviar y responder mensajes
- Gestionar adjuntos (incluyendo carga de archivos grandes por rangos)
- Administrar reglas de bandeja de entrada
- Gestionar la clasificación de enfoque (Focused Inbox)
- Trabajar con extensiones abiertas en mensajes
- Sincronizar cambios incrementales en carpetas y mensajes

### 1.2. Documentos de referencia

- [Microsoft.Graph.Mail Module (Microsoft Learn)](https://learn.microsoft.com/en-us/powershell/module/microsoft.graph.mail/?view=graph-powershell-1.0)
- [PowerShell Gallery — Microsoft.Graph.Mail](https://www.powershellgallery.com/packages/Microsoft.Graph.Mail/)
- [Outlook mail API overview (Microsoft Learn)](https://learn.microsoft.com/en-us/graph/outlook-mail-concept-overview)
- [Outlook mail API v1.0 (Microsoft Learn)](https://learn.microsoft.com/en-us/graph/api/resources/mail-api-overview)
- [Outlook mail API beta (Microsoft Learn)](https://learn.microsoft.com/en-us/graph/api/resources/mail-api-overview?view=graph-rest-beta&preserve-view=true)
- [Microsoft Graph PowerShell Overview](https://docs.microsoft.com/en-us/powershell/microsoftgraph/)

---

## 2. Instalación del Módulo

### 2.1. Instalación desde PowerShell Gallery

```powershell
# Instalar el módulo específico de Mail
Install-Module -Name Microsoft.Graph.Mail -Scope CurrentUser

# Instalar el módulo completo de Microsoft.Graph
Install-Module -Name Microsoft.Graph -Scope CurrentUser
```

### 2.2. Versiones disponibles

| Versión | Fecha | Notas |
|---------|-------|-------|
| 2.34.0 | 2025-12-20 | Última versión estable |
| 2.25.0 | — | Versión anterior |

**Documentos de referencia:**
- [PowerShell Gallery — Microsoft.Graph.Mail 2.34.0](https://www.powershellgallery.com/packages/Microsoft.Graph.Mail/2.34.0)
- [PowerShell Gallery — Microsoft.Graph.Mail 2.25.0](https://www.powershellgallery.com/packages/Microsoft.Graph.Mail/2.25.0)

---

## 3. Autenticación y Conexión a Microsoft Graph

### 3.1. Conexión con permisos delegados (usuario autenticado)

El usuario se autentica interactivamente y la aplicación actúa en su nombre.

```powershell
Connect-MgGraph -Scopes "Mail.Read", "Mail.ReadWrite", "Mail.Send"
```

### 3.2. Conexión con permisos de aplicación (daemon / sin usuario)

La aplicación se autentica con su propia identidad usando un secreto o certificado.

#### 3.2.1. Autenticación por secreto de cliente

```powershell
$AzureAppID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
$tenantID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
$clientSecret = ConvertTo-SecureString "tu-secreto" -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($AzureAppID, $clientSecret)

Connect-MgGraph -TenantId $tenantID -ClientSecretCredential $credential
```

#### 3.2.2. Autenticación por certificado

```powershell
$certThumbprint = "9CF05589A4B29BECEE6456F08A76EBC3DC2BC581"
$AzureAppID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
$tenant = "woshub.onmicrosoft.com"

Connect-MgGraph -TenantId $tenant -ClientId $AzureAppID -CertificateThumbprint $certThumbprint
```

### 3.3. Flujo OAuth2 manual con Invoke-RestMethod

Cuando se necesita más control sobre el proceso de autenticación:

```powershell
$tokenBody = @{
    Grant_Type    = "client_credentials"
    Scope         = "https://graph.microsoft.com/.default"
    Client_Id     = $AzureAppID
    Client_Secret = $AccessSecret
}
$tokenResponse = Invoke-RestMethod -Uri "https://login.microsoftonline.com/$tenantID/oauth2/v2.0/token" -Method POST -Body $tokenBody
$headers = @{
    "Authorization" = "Bearer $($tokenResponse.access_token)"
    "Content-type"  = "application/json"
}
```

### 3.4. Desconexión

```powershell
Disconnect-MgGraph
```

**Documentos de referencia:**
- [Connecting to Microsoft Graph API using PowerShell (WOSHUB)](https://woshub.com/access-azure-microsoft-graph-api-powershell/)
- [Certificate Auth for Microsoft Graph (C7Solutions)](https://c7solutions.com/2025/07/certificate-auth-for-microsoft-graph)

---

## 4. Cmdlets del Módulo — Referencia Completa

### 4.1. Gestión de Carpetas de Correo (MailFolder)

Los cmdlets de esta sección permiten gestionar las carpetas de nivel superior del buzón del usuario.

#### 4.1.1. Get-MgUserMailFolder

Obtiene las carpetas de correo del usuario.

**Sintaxis:**
```powershell
Get-MgUserMailFolder -UserId <String> [-Filter <String>] [-Select <String[]>] [-Top <Int32>]
```

**Ejemplo — Obtener la carpeta Elementos eliminados:**
```powershell
$DeletedItemsFolder = Get-MgUserMailFolder -UserId $UserUPN -Filter "displayName eq 'Deleted Items'" -Select Id
```

**Ejemplo — Listar todas las carpetas del usuario:**
```powershell
Get-MgUserMailFolder -UserId "user@domain.com" | Select-Object Id, DisplayName, UnreadItemCount, TotalItemCount
```

#### 4.1.2. Get-MgUserMailFolderCount

Obtiene el número de carpetas de correo.

```powershell
Get-MgUserMailFolderCount -UserId "user@domain.com"
```

#### 4.1.3. Get-MgUserMailFolderDelta

Obtiene un conjunto de carpetas que han sido añadidas, eliminadas o movidas desde la última consulta. Utiliza tokens de estado para sincronización incremental.

```powershell
Get-MgUserMailFolderDelta -UserId "user@domain.com"
```

#### 4.1.4. New-MgUserMailFolder

Crea una nueva carpeta de correo.

```powershell
New-MgUserMailFolder -UserId "user@domain.com" -DisplayName "Mi Nueva Carpeta"
```

#### 4.1.5. Copy-MgUserMailFolder

Copia una carpeta y todo su contenido a otra carpeta destino.

```powershell
Copy-MgUserMailFolder -UserId "user@domain.com" -MailFolderId "folderId" -DestinationId "destinationFolderId"
```

#### 4.1.6. Move-MgUserMailFolder

Mueve una carpeta y su contenido a otra ubicación.

```powershell
Move-MgUserMailFolder -UserId "user@domain.com" -MailFolderId "folderId" -DestinationId "parentFolderId"
```

#### 4.1.7. Update-MgUserMailFolder

Actualiza las propiedades de una carpeta (nombre, etc.).

```powershell
Update-MgUserMailFolder -UserId "user@domain.com" -MailFolderId "folderId" -DisplayName "Nuevo Nombre"
```

#### 4.1.8. Remove-MgUserMailFolder

Elimina una carpeta de correo.

```powershell
Remove-MgUserMailFolder -UserId "user@domain.com" -MailFolderId "folderId"
```

**Documentos de referencia:**
- [Microsoft Learn — Get-MgUserMailFolder](https://learn.microsoft.com/en-us/powershell/module/microsoft.graph.mail/get-mgusermailfolder?view=graph-powershell-1.0)
- [Get-MgUserMailFolder — M365 Corner](https://m365corner.com/m365-powershell/using-get-mgusermailfolder-in-graph-powershell.html)

---

### 4.2. Gestión de Subcarpetas (ChildFolder)

Estos cmdlets operan sobre las subcarpetas dentro de una carpeta padre.

#### 4.2.1. Get-MgUserMailFolderChildFolder

```powershell
Get-MgUserMailFolderChildFolder -UserId "user@domain.com" -MailFolderId "folderId"
```

#### 4.2.2. Get-MgUserMailFolderChildFolderCount

```powershell
Get-MgUserMailFolderChildFolderCount -UserId "user@domain.com" -MailFolderId "folderId"
```

#### 4.2.3. Get-MgUserMailFolderChildFolderDelta

Sincronización incremental de subcarpetas.

```powershell
Get-MgUserMailFolderChildFolderDelta -UserId "user@domain.com" -MailFolderId "folderId"
```

#### 4.2.4. New-MgUserMailFolderChildFolder

```powershell
New-MgUserMailFolderChildFolder -UserId "user@domain.com" -MailFolderId "folderId" -DisplayName "Subcarpeta"
```

#### 4.2.5. Copy-MgUserMailFolderChildFolder

```powershell
Copy-MgUserMailFolderChildFolder -UserId "user@domain.com" -MailFolderId "folderId" -MailFolderChildFolderId "childId" -DestinationId "destId"
```

#### 4.2.6. Move-MgUserMailFolderChildFolder

```powershell
Move-MgUserMailFolderChildFolder -UserId "user@domain.com" -MailFolderId "folderId" -MailFolderChildFolderId "childId" -DestinationId "destId"
```

#### 4.2.7. Remove-MgUserMailFolderChildFolder

```powershell
Remove-MgUserMailFolderChildFolder -UserId "user@domain.com" -MailFolderId "folderId" -MailFolderChildFolderId "childId"
```

#### 4.2.8. Update-MgUserMailFolderChildFolder

```powershell
Update-MgUserMailFolderChildFolder -UserId "user@domain.com" -MailFolderId "folderId" -MailFolderChildFolderId "childId" -DisplayName "Nuevo Nombre"
```

---

### 4.3. Lectura y Gestión de Mensajes (Message)

#### 4.3.1. Get-MgUserMessage

Recupera los mensajes del buzón del usuario. Soporta filtros, selección de propiedades y paginación.

```powershell
# Obtener todos los mensajes
Get-MgUserMessage -UserId "user@domain.com"

# Obtener mensajes con filtro
Get-MgUserMessage -UserId "user@domain.com" -Filter "receivedDateTime ge 2024-01-01T00:00:00Z"

# Seleccionar propiedades específicas
Get-MgUserMessage -UserId "user@domain.com" -Select "id,subject,from,receivedDateTime,hasAttachments,size"
```

#### 4.3.2. Get-MgUserMessageCount

```powershell
Get-MgUserMessageCount -UserId "user@domain.com"
```

#### 4.3.3. Get-MgUserMessageDelta

Obtiene cambios incrementales en los mensajes desde la última consulta. Ideal para mantener una copia local sincronizada.

```powershell
Get-MgUserMessageDelta -UserId "user@domain.com"
```

#### 4.3.4. Get-MgUserMessageContent

Recupera el contenido MIME sin procesar de un mensaje. Esencial para exportar correos completos con cabeceras, adjuntos y formato.

**Sintaxis:**
```powershell
Get-MgUserMessageContent -UserId <String> -MessageId <String> [-OutFile <String>]
```

**Ejemplo — Exportar mensaje a archivo .eml:**
```powershell
Connect-MgGraph -Scopes "Mail.Read"

$UserId = "user@domain.com"
$MessageId = "AAMkAGI2THAAA="
$OutputFile = "C:\Exports\UserEmail.eml"

$MessageContent = Get-MgUserMessageContent -UserId $UserId -MessageId $MessageId
[System.IO.File]::WriteAllBytes($OutputFile, $MessageContent)
Write-Host "Email exportado a $OutputFile"
```

**Errores comunes:**

| Error | Causa | Solución |
|-------|-------|----------|
| Invalid Message ID | El MessageId no pertenece al usuario | Verificar con `Get-MgUserMessage` |
| User Not Found | El UserId no existe | Usar `Get-MgUser` para verificar el UPN |
| File Path Error | Ruta inválida o sin permisos de escritura | Verificar el directorio de salida |

**Documentos de referencia:**
- [Get-MgUserMessageContent — M365 Corner](https://m365corner.com/m365-powershell/using-get-mgusermessagecontent-in-graph-powershell.html)
- [Microsoft Learn — Get-MgUserMessageContent](https://learn.microsoft.com/en-us/powershell/module/microsoft.graph.mail/get-mgusermessagecontent?view=graph-powershell-1.0)

#### 4.3.5. New-MgUserMessage

Crea un nuevo mensaje (borrador) en el buzón del usuario.

```powershell
New-MgUserMessage -UserId "user@domain.com" -Subject "Asunto" -Body @{ ContentType = "HTML"; Content = "<h1>Cuerpo</h1>" }
```

#### 4.3.6. Copy-MgUserMessage

Copia un mensaje a otra carpeta dentro del mismo buzón.

```powershell
Copy-MgUserMessage -UserId "user@domain.com" -MessageId "messageId" -DestinationId "folderId"
```

#### 4.3.7. Move-MgUserMessage

Mueve un mensaje a otra carpeta (elimina el original en el proceso).

```powershell
Move-MgUserMessage -UserId "user@domain.com" -MessageId "messageId" -DestinationId "folderId"
```

#### 4.3.8. Update-MgUserMessage

Actualiza las propiedades de un mensaje. **Importante**: a partir de diciembre 2026, la modificación de propiedades sensibles (subject, body, toRecipients, etc.) en mensajes no borradores requerirá el permiso `Mail-Advanced.ReadWrite`.

```powershell
Update-MgUserMessage -UserId "user@domain.com" -MessageId "messageId" -IsRead:$true
```

#### 4.3.9. Remove-MgUserMessage

```powershell
Remove-MgUserMessage -UserId "user@domain.com" -MessageId "messageId"
```

---

### 4.4. Mensajes en Carpetas Específicas (MailFolderMessage)

Operan sobre los mensajes dentro de una carpeta concreta (bandeja de entrada, elementos enviados, etc.).

#### 4.4.1. Get-MgUserMailFolderMessage

```powershell
# Obtener mensajes de la bandeja de entrada
$Inbox = Get-MgUserMailFolder -UserId "user@domain.com" -Filter "displayName eq 'Inbox'"
Get-MgUserMailFolderMessage -UserId "user@domain.com" -MailFolderId $Inbox.Id

# Obtener mensajes de Elementos eliminados
$DeletedItems = Get-MgUserMailFolder -UserId "user@domain.com" -Filter "displayName eq 'Deleted Items'"
Get-MgUserMailFolderMessage -UserId "user@domain.com" -MailFolderId $DeletedItems.Id -Select "id,subject,from,receivedDateTime"
```

#### 4.4.2. Get-MgUserMailFolderMessageCount

```powershell
Get-MgUserMailFolderMessageCount -UserId "user@domain.com" -MailFolderId "folderId"
```

#### 4.4.3. Get-MgUserMailFolderMessageDelta

```powershell
Get-MgUserMailFolderMessageDelta -UserId "user@domain.com" -MailFolderId "folderId"
```

#### 4.4.4 a 4.4.8. New, Copy, Move, Remove, Update

Siguen el mismo patrón que los cmdlets de Message pero acotados a una carpeta específica.

**Documentos de referencia:**
- [Retrieve Emails from Deleted Items Folder — M365 Corner](https://m365corner.com/m365-powershell/retrieve-emails-from-deleted-items-folder.html)
- [Get-MgUserMailFolderMessage — M365 Corner](https://m365corner.com/m365-powershell/using-get-mgusermailfoldermessage-in-graph-powershell.html)

---

### 4.5. Gestión de Adjuntos (Attachment)

#### 4.5.1. Get-MgUserMessageAttachment

Obtiene los adjuntos de un mensaje específico.

```powershell
Get-MgUserMessageAttachment -UserId "user@domain.com" -MessageId "messageId"
```

#### 4.5.2. Get-MgUserMessageAttachmentCount

```powershell
Get-MgUserMessageAttachmentCount -UserId "user@domain.com" -MessageId "messageId"
```

#### 4.5.3. New-MgUserMessageAttachment

Añade un adjunto pequeño (< 3 MB) a un mensaje.

```powershell
$AttachmentBytes = [System.IO.File]::ReadAllBytes("C:\file.pdf")
$AttachmentBase64 = [System.Convert]::ToBase64String($AttachmentBytes)

New-MgUserMessageAttachment -UserId "user@domain.com" -MessageId "messageId" -BodyParameter @{
    "@odata.type" = "#microsoft.graph.fileAttachment"
    Name = "file.pdf"
    ContentType = "application/pdf"
    ContentBytes = $AttachmentBase64
}
```

#### 4.5.4. New-MgUserMessageAttachmentUploadSession

Crea una sesión de carga para adjuntar archivos grandes (entre 3 MB y 150 MB). El proceso requiere:

1. Crear la sesión de carga
2. Subir el archivo en rangos secuenciales PUT
3. Finalizar la sesión

```powershell
New-MgUserMessageAttachmentUploadSession -UserId "user@domain.com" -MessageId "messageId" -AttachmentItem @{
    AttachmentType = "file"
    Name = "largefile.zip"
    Size = 50000000
}
```

#### 4.5.5. Remove-MgUserMessageAttachment

```powershell
Remove-MgUserMessageAttachment -UserId "user@domain.com" -MessageId "messageId" -AttachmentId "attachmentId"
```

---

### 4.6. Acciones: Envío, Reenvío y Respuesta

#### 4.6.1. Send-MgUserMail

Envía un nuevo mensaje de correo. Este cmdlet pertenece al módulo `Microsoft.Graph.Users.Actions`.

```powershell
$Message = @{
    Subject = "Hola Mundo desde Graph API"
    Body = @{
        ContentType = "HTML"
        Content     = "Este correo se envía mediante <b>Microsoft Graph API</b><br>"
    }
    ToRecipients = @(
        @{
            EmailAddress = @{ Address = "destinatario@domain.com" }
        }
    )
    Attachments = @(
        @{
            "@odata.type" = "#microsoft.graph.fileAttachment"
            Name          = "archivo.log"
            ContentType   = "application/octet-stream"
            ContentBytes  = $AttachmentBase64
        }
    )
}

Send-MgUserMail -UserId "remitente@domain.com" -Message $Message
```

#### 4.6.2. Envío mediante REST API (Invoke-RestMethod)

Alternativa que no requiere el módulo Microsoft.Graph:

```powershell
$URLsend = "https://graph.microsoft.com/v1.0/users/$MailFrom/sendMail"
$BodyJsonsend = @"
{
    "message": {
        "subject": "Test email from Microsoft Graph API",
        "body": {
            "contentType": "HTML",
            "content": "This email is sent via Microsoft GRAPH API"
        },
        "toRecipients": [
            {
                "emailAddress": {
                    "address": "$MailTo"
                }
            }
        ]
    },
    "saveToSentItems": "true"
}
"@
Invoke-RestMethod -Method POST -Uri $URLsend -Headers $headers -Body $BodyJsonsend
```

#### 4.6.3. Invoke-MgForwardUserMessage

Reenvía un mensaje existente, soportando formato JSON o MIME.

```powershell
Invoke-MgForwardUserMessage -UserId "user@domain.com" -MessageId "messageId" -Comment "Adjunto documento" -ToRecipients @(@{ EmailAddress = @{ Address = "destino@domain.com" } })
```

#### 4.6.4. Invoke-MgReplyUserMessage

Responde al remitente de un mensaje.

```powershell
Invoke-MgReplyUserMessage -UserId "user@domain.com" -MessageId "messageId" -Comment "Gracias por tu mensaje"
```

#### 4.6.5. Invoke-MgReplyAllUserMessage

Responde a todos los destinatarios del mensaje original.

```powershell
Invoke-MgReplyAllUserMessage -UserId "user@domain.com" -MessageId "messageId" -Comment "Respondiendo a todos"
```

#### 4.6.6 a 4.6.8. New-MgUserMessageForward, New-MgUserMessageReply, New-MgUserMessageReplyAll

Crean borradores para las acciones correspondientes sin enviarlos inmediatamente.

**Documentos de referencia:**
- [Send Emails with Microsoft Graph API and PowerShell (WOSHUB)](https://woshub.com/send-email-microsoft-graph-api-powershell/)
- [Send email using Microsoft Graph Mailer (WPO365)](https://docs.wpo365.com/article/141-send-email-using-microsoft-graph-mailer)

---

### 4.7. Reglas de Bandeja de Entrada (MessageRule)

Permiten gestionar las reglas que procesan automáticamente los mensajes entrantes.

| Cmdlet | Descripción |
|--------|-------------|
| `Get-MgUserMailFolderMessageRule` | Obtiene las reglas de la bandeja de entrada |
| `Get-MgUserMailFolderMessageRuleCount` | Cuenta las reglas existentes |
| `New-MgUserMailFolderMessageRule` | Crea una nueva regla |
| `Update-MgUserMailFolderMessageRule` | Actualiza una regla existente |
| `Remove-MgUserMailFolderMessageRule` | Elimina una regla |

**Ejemplo — Crear una regla que mueva correos de un remitente específico:**
```powershell
New-MgUserMailFolderMessageRule -UserId "user@domain.com" -MailFolderId "inboxFolderId" -MessageRule @{
    DisplayName = "Mover correos de jefe"
    Sequence = 1
    IsEnabled = $true
    Conditions = @{
        FromAddresses = @(@{ EmailAddress = @{ Address = "jefe@domain.com" } })
    }
    Actions = @{
        MoveToFolder = "targetFolderId"
    }
}
```

---

### 4.8. Clasificación de Enfoque (InferenceClassification)

Gestiona la funcionalidad de Bandeja de entrada Enfocada (Focused Inbox) que clasifica automáticamente los mensajes en "Enfocados" y "Otros".

| Cmdlet | Descripción |
|--------|-------------|
| `Get-MgUserInferenceClassification` | Obtiene la clasificación de enfoque del usuario |
| `Get-MgUserInferenceClassificationOverride` | Obtiene las excepciones de clasificación |
| `Get-MgUserInferenceClassificationOverrideCount` | Cuenta las excepciones |
| `New-MgUserInferenceClassificationOverride` | Crea una nueva excepción (siempre clasificar como enfocado u otro) |
| `Remove-MgUserInferenceClassificationOverride` | Elimina una excepción |
| `Update-MgUserInferenceClassificationOverride` | Actualiza una excepción |
| `Set-MgUserInferenceClassificationOverride` | Reemplaza una excepción existente |
| `Clear-MgUserInferenceClassificationOverride` | Limpia todas las excepciones |

**Ejemplo — Forzar que los correos de un remitente vayan siempre a "Enfocados":**
```powershell
New-MgUserInferenceClassificationOverride -UserId "user@domain.com" -ClassifyAs "focused" -SenderEmailAddress @{ Name = "Remitente"; Address = "remitente@domain.com" }
```

---

### 4.9. Extensiones de Mensaje

Las extensiones abiertas (openExtensions) permiten almacenar datos personalizados en los mensajes.

| Cmdlet | Descripción |
|--------|-------------|
| `Get-MgUserMessageExtension` | Obtiene las extensiones de un mensaje |
| `Get-MgUserMessageExtensionCount` | Cuenta las extensiones |
| `New-MgUserMessageExtension` | Crea una nueva extensión |
| `Update-MgUserMessageExtension` | Actualiza una extensión existente |
| `Remove-MgUserMessageExtension` | Elimina una extensión |

**Ejemplo — Añadir metadatos personalizados a un mensaje:**
```powershell
New-MgUserMessageExtension -UserId "user@domain.com" -MessageId "messageId" -ExtensionName "com.contoso.tracking" -BodyParameter @{
    "@odata.type" = "#microsoft.graph.openTypeExtension"
    extensionName = "com.contoso.tracking"
    ticketNumber = "INC-12345"
    priority = "High"
}
```

---

## 5. Permisos de Microsoft Graph para Correo

### 5.1. Permisos Estándar

| Permiso | Tipo | Descripción | ¿Requiere consentimiento admin? |
|---------|------|-------------|:---:|
| `Mail.Read` | Delegado / Aplicación | Leer correos en todos los buzones | Sí |
| `Mail.ReadBasic` | Delegado / Aplicación | Leer propiedades básicas (excluye body, previewBody, attachments, extended properties) | Sí (App) / No (Del) |
| `Mail.ReadWrite` | Delegado / Aplicación | Leer y escribir correos en todos los buzones | Sí |
| `Mail.Send` | Delegado / Aplicación | Enviar correos desde todos los buzones | Sí |
| `Mail.Read.Shared` | Delegado | Leer correos en buzones compartidos | Sí |
| `Mail.ReadWrite.Shared` | Delegado | Leer y escribir en buzones compartidos | Sí |
| `Mail.Send.Shared` | Delegado | Enviar correos desde buzones compartidos | Sí |
| `MailboxSettings.Read` | Delegado / Aplicación | Leer configuración del buzón | No (Del) / Sí (App) |
| `MailboxSettings.ReadWrite` | Delegado / Aplicación | Leer y escribir configuración del buzón | No (Del) / Sí (App) |

#### 5.1.1. Mail.Read — Propiedades de mensaje

Cuando se concede el permiso `Mail.Read`, las propiedades disponibles incluyen:

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `bccRecipients` | recipient collection | Destinatarios en copia oculta |
| `body` | itemBody | Cuerpo del mensaje (HTML o texto) |
| `bodyPreview` | String | Primeros 255 caracteres del cuerpo |
| `ccRecipients` | recipient collection | Destinatarios en copia |
| `changeKey` | String Nullable | Versión del mensaje |
| `conversationId` | String Nullable | ID de la conversación |
| `conversationIndex` | Edm.Binary Nullable | Índice de la conversación |
| `createdDateTime` | DateTimeOffset Nullable | Fecha de creación (ISO 8601 UTC) |
| `flag` | followupFlag | Estado de seguimiento |
| `from` | recipient | Propietario del buzón remitente |

### 5.2. Nuevo Permiso Avanzado — Mail-Advanced.ReadWrite (Breaking Change 2026)

**Fecha de entrada en vigor: 31 de diciembre de 2026**

Microsoft ha anunciado un cambio importante: las aplicaciones que modifiquen propiedades sensibles en mensajes que NO sean borradores necesitarán permisos elevados.

#### 5.2.1. Propiedades afectadas

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `subject` | String | Línea de asunto del mensaje |
| `body` | ItemBody | Cuerpo del mensaje (HTML o texto) |
| `toRecipients` | Recipient collection | Destinatarios Para |
| `ccRecipients` | Recipient collection | Destinatarios CC |
| `bccRecipients` | Recipient collection | Destinatarios CCO |
| `from` | Recipient | Propietario del buzón y remitente |
| `sender` | Recipient | Cuenta que generó el mensaje |
| `replyTo` | Recipient collection | Direcciones de respuesta |
| `internetMessageId` | String | ID del mensaje RFC 2822 |
| `singleValueExtendedProperties` | Collection | Propiedades extendidas de valor único |
| `multiValueExtendedProperties` | Collection | Propiedades extendidas de valor múltiple |

**Nota**: Las propiedades NO sensibles (isRead, categories, flag, importance) seguirán siendo actualizables con `Mail.ReadWrite` estándar. Los mensajes borradores NO se ven afectados.

#### 5.2.2. Nuevos permisos disponibles

| Permiso | Tipo | Descripción |
|---------|------|-------------|
| `Mail-Advanced.ReadWrite` | Delegado | Modificar propiedades sensibles en nombre del usuario autenticado |
| `Mail-Advanced.ReadWrite.All` | Aplicación | Modificar propiedades sensibles en todos los buzones sin usuario |
| `Mail-Advanced.ReadWrite.Shared` | Delegado | Modificar propiedades sensibles en buzones compartidos |

Los tres requieren **consentimiento del administrador del inquilino**.

#### 5.2.3. Guía de migración

1. **Inventariar aplicaciones**: Identificar todas las apps que usan `Mail.ReadWrite`
2. **Analizar código**: Determinar si modifican propiedades sensibles en mensajes no borradores
3. **Actualizar registros de app**: Añadir `Mail-Advanced.ReadWrite` en Azure Portal
4. **Actualizar código**: Incluir el nuevo scope en las solicitudes de autenticación
5. **Probar**: Validar en un entorno no productivo
6. **Desplegar**: Antes del 31 de diciembre de 2026

```csharp
// Antes
var scopes = new[] { "Mail.ReadWrite" };

// Después
var scopes = new[] { "Mail.ReadWrite", "Mail-Advanced.ReadWrite" };
```

**Documentos de referencia:**
- [Microsoft Graph permissions reference (Microsoft Learn)](https://learn.microsoft.com/en-us/graph/permissions-reference)
- [Graph API Breaking Change — Mike Hacker Blog](https://blog.mikehacker.net/p/graph-api-breaking-change-new-permissions-required-for-sensitive-email-properties-by-december-2026)
- [Exchange Team Announcement (DevBlogs)](https://devblogs.microsoft.com/microsoft365dev/graph-api-updates-to-sensitive-email-properties/)
- [Update message API reference](https://learn.microsoft.com/en-us/graph/api/message-update?view=graph-rest-1.0&tabs=http)
- [Graph Permissions Explorer — Mail.ReadBasic](https://permissions.cengizyilmaz.net/permissions/mail-readbasic.html)
- [Microsoft Graph national cloud deployments](https://learn.microsoft.com/en-us/graph/deployments)

---

## 6. Restricción de Acceso a Buzones

Por defecto, una aplicación con permisos `Mail.ReadWrite` o `Mail.Send` puede acceder a TODOS los buzones del inquilino. Esto raramente es deseable. Existen dos mecanismos para restringir este acceso.

### 6.1. Application Access Policy (Heredado — Exchange Online)

```powershell
# Conectar a Exchange Online
Connect-ExchangeOnline

# Crear grupo de seguridad para los buzones permitidos
New-DistributionGroup -Name "azappSendasAllowed" -Type "Security" -Members @("buzon@domain.com")
Set-DistributionGroup -Identity azappSendasAllowed -HiddenFromAddressListsEnabled $true

# Crear la política de acceso
New-ApplicationAccessPolicy -AppId "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" -PolicyScopeGroupId azappSendasAllowed -AccessRight RestrictAccess -Description "Restringir acceso a buzones específicos"

# Verificar
Test-ApplicationAccessPolicy -Identity usuario@domain.com -AppId "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### 6.2. RBAC for Applications en Exchange Online (Reemplazo moderno)

Este método usa roles de Exchange y reemplaza a Application Access Policy.

#### 6.2.1. Crear el Service Principal

```powershell
New-ServicePrincipal -AppID $AppID -ObjectID $EnterpriseAppObjectID -DisplayName "AppName RBAC for Exchange Online"
```

#### 6.2.2. Crear ámbito de gestión (Management Scope)

**Opción A — Restringir a un buzón específico:**
```powershell
$TargetMailbox = Get-Mailbox shared_app@domain.com
New-ManagementScope -Name "rbac_$AppID" -RecipientRestrictionFilter "GUID -eq '$($TargetMailbox.GUID)'"
```

**Opción B — Restringir a miembros de un grupo de distribución:**
```powershell
New-DistributionGroup "$AppName Access" -Type Security
Add-DistributionGroupMember "$AppName Access" -Member MailboxAppCanAccess
$TargetDL = Get-DistributionGroup "$AppName Access"
New-ManagementScope -Identity $AppID -RecipientRestrictionFilter "MemberOfGroup -eq '$($TargetDL.DistinguishedName)'"
```

#### 6.2.3. Asignar el rol

```powershell
New-ManagementRoleAssignment -App $AppID -Role "Application Mail.ReadWrite" -CustomResourceScope "rbac_$AppID"
```

#### 6.2.4. Roles de aplicación disponibles

Se obtienen con:
```powershell
Get-ManagementRole | Where-Object { $_.IsServicePrincipalRole } | Select-Object Name, Description | Sort-Object Name
```

Ejemplos: `Application Mail.Read`, `Application Mail.ReadWrite`, `Application Mail.Send` (14 roles en total).

#### 6.2.5. Verificación

```powershell
# Probar autorización
Test-ServicePrincipalAuthorization -Identity $AppID -Resource $TargetMailbox

# Listar asignaciones existentes
Get-ManagementRoleAssignment -RoleAssigneeType ServicePrincipal
```

**Documentos de referencia:**
- [Secure Access to Mailboxes via Graph — Brian Reid (C7Solutions)](https://c7solutions.com/2024/09/secure-access-to-mailboxes-via-graph)
- [Configure API Permissions — Intranet Connections](https://support.intranetconnections.com/hc/en-us/articles/37979916803223-Microsoft-Graph-Mail-Configuration-and-Admin-Controls)

---

## 7. Límites, Throttling y Buenas Prácticas

### 7.1. Límites de tamaño de adjuntos

| Tamaño | Método | Cmdlet |
|--------|--------|--------|
| < 3 MB | POST directo | `New-MgUserMessageAttachment` |
| 3 MB – 150 MB | Sesión de carga por rangos | `New-MgUserMessageAttachmentUploadSession` |
| > 150 MB | No soportado | — |

### 7.2. Throttling de la API

Microsoft Graph impone límites de throttling para proteger el servicio:

- **Límite por combinación (app + mailbox)**: 150 MB de datos subidos cada 5 minutos
- **Superación del límite**: Error `ApplicationThrottled` con mensaje "Application is over its IncomingBytes limit"

### 7.3. Buenas prácticas

1. **Solicitar el mínimo permiso necesario**: No conceder `Mail.ReadWrite` si solo se necesita `Mail.Send`
2. **Usar filtros y selección de propiedades**: Limitar los datos recuperados con `-Filter` y `-Select`
3. **Implementar paginación**: Usar `-Top` y `-Skip` para conjuntos grandes de resultados
4. **Usar delta queries**: Preferir `Get-MgUserMessageDelta` para sincronización en lugar de recuperar todo cada vez
5. **Gestionar errores**: Implementar lógica de reintento con backoff exponencial ante errores de throttling
6. **Restringir acceso a buzones**: Usar RBAC for Applications en lugar de permitir acceso a todos los buzones

**Documentos de referencia:**
- [Throttling limits (Microsoft Learn)](https://learn.microsoft.com/en-us/graph/throttling-limits)
- [Microsoft Q&A — Envío de correos > 150 MB](https://learn.microsoft.com/en-us/answers/questions/1730503/when-sending-emails-using-microsoft-graph-api-what)
- [Filter Email Messages (UserComp)](https://usercomp.com/news/1400766/filter-emails-with-microsoft-graph-api)

---

## 8. Casos de Uso Prácticos

### 8.1. Auditoría de la carpeta Elementos eliminados

```powershell
Connect-MgGraph -Scopes "Mail.Read"

$UserUPN = "user@domain.com"
$DeletedItemsFolder = Get-MgUserMailFolder -UserId $UserUPN -Filter "displayName eq 'Deleted Items'" -Select Id

if (-not $DeletedItemsFolder) {
    Write-Output "Carpeta Elementos eliminados no encontrada."
    Disconnect-MgGraph
    return
}

$DeletedEmails = Get-MgUserMailFolderMessage -UserId $UserUPN -MailFolderId $DeletedItemsFolder.Id -Select "id,subject,from,receivedDateTime"

$DeletedEmails | Select-Object @{Name="Remitente";Expression={$_.From.EmailAddress.Address}}, Subject, ReceivedDateTime |
    Export-Csv -Path "DeletedItemsReport.csv" -NoTypeInformation

Disconnect-MgGraph
```

### 8.2. Archivado forense de un mensaje

```powershell
Connect-MgGraph -Scopes "Mail.Read"

$UserId = "user@domain.com"
$MessageId = "AAMkADk3ZGMxNjZiLTU3YYwnbJQNhSTOqVwBGZBvXKAABTc36rAAA="
$OutputFile = "C:\Evidencias\correo_forense.eml"

$MessageContent = Get-MgUserMessageContent -UserId $UserId -MessageId $MessageId
[System.IO.File]::WriteAllBytes($OutputFile, $MessageContent)
Write-Host "Correo exportado a $OutputFile"

Disconnect-MgGraph
```

### 8.3. Envío automático de notificaciones

```powershell
Connect-MgGraph -TenantId $tenantID -ClientId $AzureAppID -CertificateThumbprint $certThumbprint

$MailFrom = "noreply@domain.com"
$MailTo = "usuario@domain.com"

$Message = @{
    Subject = "Notificación automática"
    Body = @{
        ContentType = "HTML"
        Content     = "<h1>Aviso importante</h1><p>Esto es una notificación automática.</p>"
    }
    ToRecipients = @(@{ EmailAddress = @{ Address = $MailTo } })
}

Send-MgUserMail -UserId $MailFrom -Message $Message
Disconnect-MgGraph
```

### 8.4. Sincronización incremental de mensajes

```powershell
Connect-MgGraph -Scopes "Mail.Read"

$UserId = "user@domain.com"
# Primera llamada: obtener todos los mensajes y un token delta
$messages = Get-MgUserMessageDelta -UserId $UserId
$deltaToken = $messages.DeltaLink

# Exportar mensajes
$messages | Export-Csv -Path "mensajes_base.csv" -NoTypeInformation

# En llamadas posteriores: solo cambios desde la última vez
$newMessages = Invoke-MgGraphRequest -Uri $deltaToken -Method GET

Disconnect-MgGraph
```

### 8.5. Aplicar reglas de bandeja de entrada mediante script

```powershell
Connect-MgGraph -Scopes "Mail.ReadWrite"

$UserId = "user@domain.com"
$Inbox = Get-MgUserMailFolder -UserId $UserId -Filter "displayName eq 'Inbox'"

# Crear carpeta destino
$TargetFolder = New-MgUserMailFolder -UserId $UserId -DisplayName "Correos del Jefe"

# Crear regla
New-MgUserMailFolderMessageRule -UserId $UserId -MailFolderId $Inbox.Id -MessageRule @{
    DisplayName = "Organizar correos del jefe"
    Sequence = 1
    IsEnabled = $true
    Conditions = @{
        FromAddresses = @(@{ EmailAddress = @{ Address = "jefe@domain.com" } })
    }
    Actions = @{
        MoveToFolder = $TargetFolder.Id
        MarkImportance = "high"
    }
}

Disconnect-MgGraph
```

---

## 9. Referencias

### 9.1. Documentación oficial

| Recurso | URL |
|---------|-----|
| Microsoft.Graph.Mail Module | https://learn.microsoft.com/en-us/powershell/module/microsoft.graph.mail/ |
| PowerShell Gallery | https://www.powershellgallery.com/packages/Microsoft.Graph.Mail/ |
| Outlook mail API overview | https://learn.microsoft.com/en-us/graph/outlook-mail-concept-overview |
| Permissions reference | https://learn.microsoft.com/en-us/graph/permissions-reference |
| Throttling limits | https://learn.microsoft.com/en-us/graph/throttling-limits |
| Microsoft Graph PowerShell Overview | https://docs.microsoft.com/en-us/powershell/microsoftgraph/ |
| Microsoft Graph API Overview | https://docs.microsoft.com/en-us/graph/api/overview |

### 9.2. Artículos técnicos

| Recurso | URL |
|---------|-----|
| Send Emails with Graph API (WOSHUB) | https://woshub.com/send-email-microsoft-graph-api-powershell/ |
| Get-MgUserMessageContent (M365 Corner) | https://m365corner.com/m365-powershell/using-get-mgusermessagecontent-in-graph-powershell.html |
| Deleted Items (M365 Corner) | https://m365corner.com/m365-powershell/retrieve-emails-from-deleted-items-folder.html |
| Get-MgUserMailFolder (M365 Corner) | https://m365corner.com/m365-powershell/using-get-mgusermailfolder-in-graph-powershell.html |
| Get-MgUserMailFolderMessage (M365 Corner) | https://m365corner.com/m365-powershell/using-get-mgusermailfoldermessage-in-graph-powershell.html |
| Secure Access to Mailboxes (C7Solutions) | https://c7solutions.com/2024/09/secure-access-to-mailboxes-via-graph |
| Breaking Change Mail-Advanced (Mike Hacker) | https://blog.mikehacker.net/p/graph-api-breaking-change-new-permissions-required-for-sensitive-email-properties-by-december-2026 |
| Graph Mailer (WPO365) | https://docs.wpo365.com/article/141-send-email-using-microsoft-graph-mailer |
| Filter Messages (UserComp) | https://usercomp.com/news/1400766/filter-emails-with-microsoft-graph-api |
| Certificate Auth (C7Solutions) | https://c7solutions.com/2025/07/certificate-auth-for-microsoft-graph |
| Exchange Team Announcement (DevBlogs) | https://devblogs.microsoft.com/microsoft365dev/graph-api-updates-to-sensitive-email-properties/ |

### 9.3. Herramientas

| Recurso | URL |
|---------|-----|
| Graph Permissions Explorer | https://permissions.cengizyilmaz.net/permissions/mail-readbasic.html |
| Cmdlet Finder (M365 Corner) | https://m365corner.com/graph-cmdlet-finder.html |
| Graph Explorer | https://developer.microsoft.com/en-us/graph/graph-explorer |
| National Cloud Deployments | https://learn.microsoft.com/en-us/graph/deployments |

---

## 10. Anexo: Errores y Problemas Detectados

Este anexo recopila los errores más comunes al trabajar con el módulo `Microsoft.Graph.Mail`, organizados por categoría, incluyendo causas, soluciones y referencias.

### 10.1. Errores de Autenticación y Autorización

#### 10.1.1. Connect-MgGraph no reconocido

| Aspecto | Detalle |
|---------|---------|
| **Error** | `Connect-MgGraph: The term 'Connect-MgGraph' is not recognized as the name of a cmdlet` |
| **Causa** | El módulo `Microsoft.Graph.Authentication` no está instalado o no se ha importado |
| **Solución** | Ejecutar `Install-Module Microsoft.Graph.Authentication -Scope CurrentUser` e `Import-Module Microsoft.Graph.Authentication` |
| **Referencia** | [Stack Overflow](https://stackoverflow.com/questions/78920059) |

#### 10.1.2. One or more errors occurred

| Aspecto | Detalle |
|---------|---------|
| **Error** | `Connect-MgGraph: One or more errors occurred.` |
| **Causa** | El módulo `Microsoft.Graph.Authentication` está obsoleto o no se ha importado correctamente |
| **Solución** | Actualizar el módulo: `Update-Module Microsoft.Graph.Authentication`. Si persiste, reinstalar: `Uninstall-Module Microsoft.Graph.Authentication -AllVersions` seguido de `Install-Module Microsoft.Graph.Authentication` |
| **Referencia** | [Microsoft Learn Q&A](https://learn.microsoft.com/en-us/answers/questions/1823660) |

#### 10.1.3. InvalidAuthenticationToken

| Aspecto | Detalle |
|---------|---------|
| **Error** | `InvalidAuthenticationToken: Access token is empty, expired, or malformed` |
| **Causa** | El token de acceso ha expirado (válido por 60-90 minutos por defecto), o no se ha solicitado con los scopes correctos |
| **Solución** | Llamar a `Connect-MgGraph` de nuevo para renovar el token. Verificar que los scopes incluyen los permisos necesarios |
| **Referencia** | [Microsoft Graph Auth Errors](https://learn.microsoft.com/en-us/graph/auth/auth-concepts) |

#### 10.1.4. No service connection found

| Aspecto | Detalle |
|---------|---------|
| **Error** | `No service connection found. Use Connect-MgGraph to establish a connection.` |
| **Causa** | No hay una sesión activa de Microsoft Graph |
| **Solución** | Ejecutar `Connect-MgGraph` con los scopes adecuados antes de usar cualquier cmdlet |
| **Referencia** | Documentación de Microsoft.Graph.Authentication |

#### 10.1.5. Token acquisition failed (AADSTS700016)

| Aspecto | Detalle |
|---------|---------|
| **Error** | `AADSTS700016: Application with identifier was not found in the directory` |
| **Causa** | El Application ID o el Tenant ID son incorrectos, o la aplicación no está registrada en el inquilino |
| **Solución** | Verificar el Application ID en Azure Portal > App Registrations. Confirmar que el Tenant ID corresponde al inquilino correcto |
| **Referencia** | [AADSTS error codes](https://learn.microsoft.com/en-us/entra/identity-platform/reference-error-codes) |

### 10.2. Errores de Instalación del Módulo

#### 10.2.1. PackageManagement\Install-Package: No match was found

| Aspecto | Detalle |
|---------|---------|
| **Error** | `No match was found for the specified search criteria for the module 'Microsoft.Graph.Mail'` |
| **Causa** | El repositorio PSGallery no está configurado como trusted, o la versión de PowerShell es anterior a la 5.0 |
| **Solución** | Ejecutar `Set-PSRepository -Name PSGallery -InstallationPolicy Trusted` y verificar la versión con `$PSVersionTable.PSVersion` |
| **Referencia** | [PowerShell Gallery troubleshooting](https://learn.microsoft.com/en-us/powershell/gallery/getting-started) |

#### 10.2.2. Dependency conflicts entre módulos

| Aspecto | Detalle |
|---------|---------|
| **Error** | Advertencias de dependencias incompatibles entre `Microsoft.Graph.Mail` y otros sub-módulos de Microsoft.Graph |
| **Causa** | Versiones mixtas de módulos Microsoft.Graph.* instaladas simultáneamente |
| **Solución** | Instalar desde la raíz: `Install-Module Microsoft.Graph -Scope CurrentUser` que instala todos los sub-módulos con versiones consistentes |
| **Referencia** | [Microsoft.Graph PowerShell docs](https://learn.microsoft.com/en-us/powershell/microsoftgraph/installation) |

### 10.3. Errores en Operaciones con Cmdlets

#### 10.3.1. Get-MgUserMessage devuelve body vacío

| Aspecto | Detalle |
|---------|---------|
| **Error** | La propiedad `Body.Content` aparece vacía o como `System.Object[]` |
| **Causa** | El cuerpo del mensaje no se incluye por defecto en la respuesta. Es una propiedad expandible que debe solicitarse explícitamente |
| **Solución** | Usar `-Select Body` o `-Property Body` en el cmdlet. Ejemplo: `Get-MgUserMessage -UserId "user@domain.com" -Select "id,subject,body"` |
| **Referencia** | [GitHub Issue #2404](https://github.com/microsoftgraph/msgraph-sdk-powershell/issues/2404) |

#### 10.3.2. 400 Bad Request en Send-MgUserMail

| Aspecto | Detalle |
|---------|---------|
| **Error** | `Send-MgUserMail: 400 Bad Request` o `Response status code does not indicate success: 400 (BadRequest)` |
| **Causa** | El JSON del mensaje está mal formado (generalmente el hashtable anidado de Body, ToRecipients o Attachments tiene una estructura incorrecta) |
| **Solución** | 1) Verificar que `Body.ContentType` sea "HTML" o "Text", 2) Verificar que `ToRecipients` contenga `@{ EmailAddress = @{ Address = "..." } }`, 3) Usar `ConvertTo-Json` para depurar la estructura. Ejemplo diagnóstico: `$Message | ConvertTo-Json -Depth 5` |
| **Referencia** | [Stack Overflow](https://stackoverflow.com/questions/71188522), [WOSHUB](https://woshub.com/send-email-microsoft-graph-api-powershell/) |

#### 10.3.3. 403 Forbidden — Insufficient privileges

| Aspecto | Detalle |
|---------|---------|
| **Error** | `Insufficient privileges to complete the operation.` |
| **Causa** | La aplicación no tiene los permisos adecuados concedidos, o el usuario autenticado no tiene licencia de Exchange Online |
| **Solución** | 1) Verificar permisos en Azure Portal: API Permissions > Microsoft Graph > añadir permisos de tipo Application o Delegated según corresponda, 2) Ejecutar `Connect-MgGraph` con los scopes correctos, 3) Verificar que el usuario tenga licencia de Exchange Online. Para permisos de aplicación, asegurar que el admin ha concedido consentimiento |
| **Referencia** | [Microsoft Learn — permissions-reference](https://learn.microsoft.com/en-us/graph/permissions-reference) |

#### 10.3.4. 404 Resource not found — Mailbox does not exist

| Aspecto | Detalle |
|---------|---------|
| **Error** | `ResourceNotFound: The specified mailbox does not exist` |
| **Causa** | El buzón del usuario no existe (usuario sin licencia Exchange Online, o UPN incorrecto) |
| **Solución** | Verificar con `Get-MgUser -UserId "user@domain.com"` que el usuario existe y tiene licencia. Usar `Get-MgUserMailFolder` para confirmar que el buzón es accesible |

#### 10.3.5. Error al adjuntar archivos

| Aspecto | Detalle |
|---------|---------|
| **Error** | `Request entity too large` (413) o `Attachment size exceeds the maximum allowed` |
| **Causa** | Adjunto superior a 3 MB enviado directamente con `New-MgUserMessageAttachment` en lugar de usar sesión de carga |
| **Solución** | Para archivos > 3 MB, usar `New-MgUserMessageAttachmentUploadSession`. Para archivos > 150 MB, no es posible adjuntar mediante Microsoft Graph |
| **Referencia** | [Microsoft Learn — attachment limits](https://learn.microsoft.com/en-us/graph/api/resources/attachment) |

### 10.4. Errores de Throttling y Límites

#### 10.4.1. ApplicationThrottled / TooManyRequests (429)

| Aspecto | Detalle |
|---------|---------|
| **Error** | `Application is over its IncomingBytes limit` o `Too Many Requests` (HTTP 429) |
| **Causa** | Se ha excedido el límite de 150 MB de datos subidos en 5 minutos para la combinación app + buzón |
| **Solución** | 1) Implementar backoff exponencial: esperar y reintentar, 2) Espaciar las operaciones de escritura en lotes más pequeños a lo largo del tiempo, 3) Monitorizar cabeceras `Retry-After` en la respuesta |
| **Referencia** | [Microsoft Learn — throttling-limits](https://learn.microsoft.com/en-us/graph/throttling-limits) |

#### 10.4.2. Resource locked / Concurrent modification

| Aspecto | Detalle |
|---------|---------|
| **Error** | `The item was updated by another user` o errores de conflicto `HTTP 409 Conflict` |
| **Causa** | Múltiples aplicaciones o usuarios modificando el mismo mensaje simultáneamente |
| **Solución** | 1) Usar la propiedad `changeKey` para detectar cambios concurrentes, 2) Implementar optimistic concurrency: leer cambioKey antes de modificar, 3) Reintentar la operación si falla |

### 10.5. Problemas con Delta Queries

#### 10.5.1. Pérdida de notificaciones con Immutable IDs

| Aspecto | Detalle |
|---------|---------|
| **Error** | Las delta queries pierden cambios entre consultas, o los tokens delta expiran inesperadamente |
| **Causa** | Microsoft recomienda usar Immutable IDs para delta queries, pero los tokens delta pueden invalidarse si los datos subyacentes cambian significativamente |
| **Solución** | 1) Almacenar el `DeltaLink` después de cada consulta exitosa, 2) Si el token expira, reiniciar con una consulta completa: `Get-MgUserMessageDelta -UserId "user@domain.com"` sin token, 3) Implementar lógica de reinicio automático |
| **Referencia** | [Microsoft Graph delta query docs](https://learn.microsoft.com/en-us/graph/delta-query-overview) |

### 10.6. Errores de Conectividad y Red

#### 10.6.1. API temporarily unavailable (503)

| Aspecto | Detalle |
|---------|---------|
| **Error** | `Service Unavailable` (HTTP 503) |
| **Causa** | El servicio de Microsoft Graph está temporalmente no disponible por mantenimiento o sobrecarga |
| **Solución** | 1) Esperar y reintentar con backoff exponencial, 2) Consultar el estado del servicio en [Microsoft 365 Health Dashboard](https://admin.microsoft.com/Adminportal/Home#/servicehealth) |

#### 10.6.2. Timeout / Endpoint not reachable

| Aspecto | Detalle |
|---------|---------|
| **Error** | La conexión con graph.microsoft.com no se puede establecer, o se agota el tiempo de espera |
| **Causa** | Problemas de conectividad de red, proxy corporativo, firewall, o resolución DNS |
| **Solución** | 1) Verificar conectividad: `Test-NetConnection graph.microsoft.com -Port 443`, 2) Configurar proxy en PowerShell si es necesario: `[System.Net.WebRequest]::DefaultWebProxy = New-Object System.Net.WebProxy("http://proxy:8080")`, 3) Verificar que el firewall permite salida HTTPS a `graph.microsoft.com` |

### 10.7. Problemas de Permisos y Breaking Changes

#### 10.7.1. Mail-Advanced.ReadWrite no concedido (Dic 2026+)

| Aspecto | Detalle |
|---------|---------|
| **Error** | A partir de diciembre 2026, las operaciones de `Update-MgUserMessage` que modifiquen propiedades sensibles (subject, body, toRecipients, etc.) en mensajes no borradores fallarán si no se tiene `Mail-Advanced.ReadWrite` |
| **Causa** | Breaking change anunciado por Microsoft (ver Sección 5.2) |
| **Solución** | Antes del 31/12/2026: añadir el permiso en Azure Portal y en el código. Después: las aplicaciones sin el permiso no podrán modificar mensajes enviados/recibidos |
| **Referencia** | [Mike Hacker Blog](https://blog.mikehacker.net/p/graph-api-breaking-change-new-permissions-required-for-sensitive-email-properties-by-december-2026), [DevBlogs](https://devblogs.microsoft.com/microsoft365dev/graph-api-updates-to-sensitive-email-properties/) |

#### 10.7.2. Application Access Policy vs RBAC

| Aspecto | Detalle |
|---------|---------|
| **Problema** | `ApplicationAccessPolicy` (método heredado) puede no funcionar para ciertos tipos de buzones (compartidos, de sala, etc.) |
| **Causa** | Application Access Policy fue el mecanismo original, pero Microsoft recomienda migrar a RBAC for Applications en Exchange Online |
| **Solución** | Migrar a RBAC for Applications (ver Sección 6.2). Verificar con `Test-ServicePrincipalAuthorization` |
| **Referencia** | [C7Solutions](https://c7solutions.com/2024/09/secure-access-to-mailboxes-via-graph) |

### 10.8. Errores de Rendimiento

#### 10.8.1. Lentitud en consultas sin filtros

| Aspecto | Detalle |
|---------|---------|
| **Problema** | `Get-MgUserMessage` sin filtro tarda mucho o devuelve demasiados datos |
| **Causa** | Sin filtros ni selección de propiedades, el cmdlet recupera todas las propiedades de todos los mensajes del buzón |
| **Solución** | 1) Usar `-Filter` (ej: `receivedDateTime ge 2024-01-01T00:00:00Z`), 2) Usar `-Select` para limitar propiedades, 3) Usar `-Top` para limitar número de resultados, 4) Considerar `Get-MgUserMessageDelta` para sincronización incremental |
| **Referencia** | [UserComp](https://usercomp.com/news/1400766/filter-emails-with-microsoft-graph-api) |

#### 10.8.2. Paginación incompleta

| Aspecto | Detalle |
|---------|---------|
| **Problema** | El cmdlet no devuelve todos los resultados, solo los primeros 100-1000 |
| **Causa** | Microsoft Graph devuelve resultados paginados por defecto (100 elementos por página). El SDK de PowerShell a veces no sigue automáticamente el `@odata.nextLink` |
| **Solución** | 1) Usar `-PageSize` para aumentar el tamaño de página (máximo 1000), 2) Implementar paginación manual siguiendo el `@odata.nextLink` con `Invoke-MgGraphRequest`, 3) Documentación en la sección 7.3 |

### 10.9. Problemas Específicos de Entorno

| Problema | Entorno | Causa | Solución |
|----------|---------|-------|----------|
| `Method not found: 'Void System.Net.Http.HttpClientHandler.set_ServerCertificateCustomValidationCallback'` | Windows PowerShell 5.1 | .NET Framework incompatible con el SDK moderno | Migrar a PowerShell 7+ |
| `Could not load type 'Microsoft.Identity.Client ...'` | Multi-versión | Conflictos entre versiones de Microsoft.Identity.Client | Limpiar y reinstalar módulos Microsoft.Graph.* |
| Errores en nubes soberanas (GCC, national clouds) | Government / Nacional | Endpoints diferentes a graph.microsoft.com | Usar `-Environment` en `Connect-MgGraph`: `Connect-MgGraph -Environment USGov` |
| Error al usar `Disconnect-MgGraph` en scripts CI/CD | CI/CD | No hay contexto de sesión interactiva | Usar solo autenticación por certificado o secreto en CI/CD |

### 10.10. Checklist de Diagnóstico Rápido

Ante un error, seguir esta secuencia:

1. **¿Está conectado?** `Get-MgContext` — si no hay contexto, ejecutar `Connect-MgGraph`
2. **¿Está instalado el módulo?** `Get-InstalledModule Microsoft.Graph.Mail` — si no, `Install-Module Microsoft.Graph.Mail`
3. **¿Tiene los permisos correctos?** Verificar en Azure Portal: API Permissions > Microsoft Graph
4. **¿El usuario tiene licencia Exchange Online?** Verificar en M365 Admin Center > Usuarios > Licencias
5. **¿El JSON está bien formado?** `$variable | ConvertTo-Json -Depth 5` y revisar la estructura
6. **¿Es un error de throttling?** Revisar cabeceras HTTP `Retry-After` y esperar
7. **¿El token ha expirado?** Los tokens de acceso expiran a los 60-90 minutos. Reconectar con `Connect-MgGraph`
8. **¿Es un breaking change conocido?** Consultar [Microsoft Graph changelog](https://learn.microsoft.com/en-us/graph/changelog)

**Referencias de errores:**

| Recurso | URL |
|---------|-----|
| Microsoft Graph Known Issues | https://learn.microsoft.com/en-us/graph/known-issues |
| Interface de seguimiento de problemas | https://learn.microsoft.com/en-us/graph/troubleshoot-known-issues |
| Microsoft Q&A: Microsoft Graph | https://learn.microsoft.com/en-us/answers/tags/214/graph |
| GitHub Issues: PowerShell SDK | https://github.com/microsoftgraph/msgraph-sdk-powershell/issues |
| Stack Overflow: microsoft-graph | https://stackoverflow.com/questions/tagged/microsoft-graph |
| Microsoft Graph Changelog | https://learn.microsoft.com/en-us/graph/changelog |
| Microsoft 365 Service Health | https://admin.microsoft.com/Adminportal/Home#/servicehealth |
