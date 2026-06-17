# Microsoft.Graph.Mail — Referencia de Documentación

## 1. Introducción al Módulo Microsoft.Graph.Mail

El módulo `Microsoft.Graph.Mail` forma parte del SDK de PowerShell para Microsoft Graph v1.0. Proporciona cmdlets para gestionar buzones, carpetas, mensajes de correo, reglas de bandeja de entrada, clasificación de enfoque y adjuntos en Exchange Online a través de la API de Outlook Mail de Microsoft Graph.

**Documentos de referencia:**
- [Microsoft.Graph.Mail Module (Microsoft Learn)](https://learn.microsoft.com/en-us/powershell/module/microsoft.graph.mail/?view=graph-powershell-1.0)
- [PowerShell Gallery — Microsoft.Graph.Mail](https://www.powershellgallery.com/packages/Microsoft.Graph.Mail/)
- [Outlook mail API overview (Microsoft Learn)](https://learn.microsoft.com/en-us/graph/outlook-mail-concept-overview)
- [Outlook mail API — v1.0 reference](https://learn.microsoft.com/en-us/graph/api/resources/mail-api-overview)
- [Outlook mail API — beta reference](https://learn.microsoft.com/en-us/graph/api/resources/mail-api-overview?view=graph-rest-beta&preserve-view=true)

---

## 2. Cmdlets del Módulo Microsoft.Graph.Mail

### 2.1. Gestión de Carpetas de Correo (MailFolder)

| Cmdlet | Descripción |
|--------|-------------|
| `Get-MgUserMailFolder` | Obtiene las carpetas de correo del buzón del usuario |
| `Get-MgUserMailFolderCount` | Obtiene el número de carpetas de correo |
| `Get-MgUserMailFolderDelta` | Obtiene cambios incrementales en las carpetas |
| `New-MgUserMailFolder` | Crea una nueva carpeta de correo |
| `Copy-MgUserMailFolder` | Copia una carpeta y su contenido a otra carpeta |
| `Move-MgUserMailFolder` | Mueve una carpeta y su contenido a otra carpeta |
| `Update-MgUserMailFolder` | Actualiza las propiedades de una carpeta |
| `Remove-MgUserMailFolder` | Elimina una carpeta de correo |

**Documentos de referencia:**
- [Get-MgUserMailFolder — M365 Corner](https://m365corner.com/m365-powershell/using-get-mgusermailfolder-in-graph-powershell.html)
- [Microsoft Learn — Get-MgUserMailFolder](https://learn.microsoft.com/en-us/powershell/module/microsoft.graph.mail/get-mgusermailfolder?view=graph-powershell-1.0)

### 2.2. Gestión de Subcarpetas (ChildFolder)

| Cmdlet | Descripción |
|--------|-------------|
| `Get-MgUserMailFolderChildFolder` | Obtiene las subcarpetas de una carpeta |
| `Get-MgUserMailFolderChildFolderCount` | Obtiene el número de subcarpetas |
| `Get-MgUserMailFolderChildFolderDelta` | Obtiene cambios incrementales en subcarpetas |
| `New-MgUserMailFolderChildFolder` | Crea una nueva subcarpeta |
| `Copy-MgUserMailFolderChildFolder` | Copia una subcarpeta y su contenido |
| `Move-MgUserMailFolderChildFolder` | Mueve una subcarpeta a otra ubicación |
| `Remove-MgUserMailFolderChildFolder` | Elimina una subcarpeta |
| `Update-MgUserMailFolderChildFolder` | Actualiza propiedades de una subcarpeta |

### 2.3. Lectura y Gestión de Mensajes (Message)

| Cmdlet | Descripción |
|--------|-------------|
| `Get-MgUserMessage` | Obtiene los mensajes del buzón del usuario |
| `Get-MgUserMessageCount` | Obtiene el número de mensajes |
| `Get-MgUserMessageDelta` | Obtiene cambios incrementales en los mensajes |
| `Get-MgUserMessageContent` | Recupera el contenido MIME sin procesar de un mensaje |
| `New-MgUserMessage` | Crea un nuevo mensaje |
| `Copy-MgUserMessage` | Copia un mensaje a otra carpeta |
| `Move-MgUserMessage` | Mueve un mensaje a otra carpeta |
| `Update-MgUserMessage` | Actualiza las propiedades de un mensaje |
| `Remove-MgUserMessage` | Elimina un mensaje |
| `Send-MgUserMessage` | Envía un mensaje existente en la carpeta Borradores |

**Documentos de referencia:**
- [Get-MgUserMessageContent — M365 Corner](https://m365corner.com/m365-powershell/using-get-mgusermessagecontent-in-graph-powershell.html)
- [Microsoft Learn — Get-MgUserMessageContent](https://learn.microsoft.com/en-us/powershell/module/microsoft.graph.mail/get-mgusermessagecontent?view=graph-powershell-1.0)

### 2.4. Mensajes en Carpetas Específicas (MailFolderMessage)

| Cmdlet | Descripción |
|--------|-------------|
| `Get-MgUserMailFolderMessage` | Obtiene los mensajes dentro de una carpeta específica |
| `Get-MgUserMailFolderMessageCount` | Cuenta los mensajes de una carpeta |
| `Get-MgUserMailFolderMessageDelta` | Cambios incrementales en los mensajes de una carpeta |
| `New-MgUserMailFolderMessage` | Crea un nuevo mensaje en una carpeta |
| `Copy-MgUserMailFolderMessage` | Copia un mensaje dentro del buzón |
| `Move-MgUserMailFolderMessage` | Mueve un mensaje a otra carpeta |
| `Remove-MgUserMailFolderMessage` | Elimina un mensaje de una carpeta |
| `Update-MgUserMailFolderMessage` | Actualiza propiedades de un mensaje en una carpeta |

**Documentos de referencia:**
- [Retrieve Emails from Deleted Items — M365 Corner](https://m365corner.com/m365-powershell/retrieve-emails-from-deleted-items-folder.html)
- [Get-MgUserMailFolderMessage — M365 Corner](https://m365corner.com/m365-powershell/using-get-mgusermailfoldermessage-in-graph-powershell.html)

### 2.5. Adjuntos (Attachment)

| Cmdlet | Descripción |
|--------|-------------|
| `Get-MgUserMessageAttachment` | Obtiene los adjuntos de un mensaje |
| `Get-MgUserMessageAttachmentCount` | Cuenta los adjuntos de un mensaje |
| `New-MgUserMessageAttachment` | Añade un adjunto a un mensaje |
| `New-MgUserMessageAttachmentUploadSession` | Crea una sesión de carga para archivos grandes (3 MB – 150 MB) |
| `Remove-MgUserMessageAttachment` | Elimina un adjunto de un mensaje |

### 2.6. Acciones sobre Mensajes: Envío, Reenvío y Respuesta

| Cmdlet | Descripción |
|--------|-------------|
| `Send-MgUserMail` | Envía un nuevo mensaje de correo (pertenece a Microsoft.Graph.Users.Actions) |
| `Invoke-MgForwardUserMessage` | Reenvía un mensaje (JSON o MIME) |
| `Invoke-MgReplyUserMessage` | Responde al remitente de un mensaje |
| `Invoke-MgReplyAllUserMessage` | Responde a todos los destinatarios de un mensaje |
| `New-MgUserMessageForward` | Crea un borrador para reenviar un mensaje |
| `New-MgUserMessageReply` | Crea un borrador para responder al remitente |
| `New-MgUserMessageReplyAll` | Crea un borrador para responder a todos |

**Documentos de referencia:**
- [Send Emails with Microsoft Graph API and PowerShell (WOSHUB)](https://woshub.com/send-email-microsoft-graph-api-powershell/)
- Envío con `Send-MgUserMail` (sección 3 del artículo de WOSHUB)
- Envío con `Invoke-RestMethod` + REST API (sección 2 del artículo de WOSHUB)

### 2.7. Reglas de Bandeja de Entrada (MessageRule)

| Cmdlet | Descripción |
|--------|-------------|
| `Get-MgUserMailFolderMessageRule` | Obtiene las reglas de la bandeja de entrada |
| `Get-MgUserMailFolderMessageRuleCount` | Cuenta las reglas |
| `New-MgUserMailFolderMessageRule` | Crea una nueva regla de bandeja de entrada |
| `Update-MgUserMailFolderMessageRule` | Actualiza una regla existente |
| `Remove-MgUserMailFolderMessageRule` | Elimina una regla |

### 2.8. Clasificación de Enfoque (InferenceClassification)

| Cmdlet | Descripción |
|--------|-------------|
| `Get-MgUserInferenceClassification` | Obtiene la clasificación de enfoque del usuario |
| `Get-MgUserInferenceClassificationOverride` | Obtiene las excepciones de clasificación |
| `Get-MgUserInferenceClassificationOverrideCount` | Cuenta las excepciones |
| `New-MgUserInferenceClassificationOverride` | Crea una nueva excepción de clasificación |
| `Remove-MgUserInferenceClassificationOverride` | Elimina una excepción |
| `Update-MgUserInferenceClassificationOverride` | Actualiza una excepción existente |
| `Set-MgUserInferenceClassificationOverride` | Reemplaza una excepción existente |
| `Clear-MgUserInferenceClassificationOverride` | Limpia todas las excepciones |

### 2.9. Extensiones de Mensaje

| Cmdlet | Descripción |
|--------|-------------|
| `Get-MgUserMessageExtension` | Obtiene las extensiones abiertas de un mensaje |
| `Get-MgUserMessageExtensionCount` | Cuenta las extensiones |
| `New-MgUserMessageExtension` | Crea una nueva extensión abierta |
| `Update-MgUserMessageExtension` | Actualiza una extensión |
| `Remove-MgUserMessageExtension` | Elimina una extensión |

---

## 3. Permisos de Microsoft Graph para Correo

### 3.1. Permisos Estándar de Correo

| Permiso | Tipo | Descripción |
|---------|------|-------------|
| `Mail.Read` | Delegado / Aplicación | Leer correos en todos los buzones |
| `Mail.ReadBasic` | Delegado / Aplicación | Leer propiedades básicas (excluye body, previewBody, attachments) |
| `Mail.ReadWrite` | Delegado / Aplicación | Leer y escribir correos en todos los buzones |
| `Mail.Send` | Delegado / Aplicación | Enviar correos desde todos los buzones |
| `Mail.Read.Shared` | Delegado | Leer correos en buzones compartidos |
| `Mail.ReadWrite.Shared` | Delegado | Leer y escribir en buzones compartidos |
| `Mail.Send.Shared` | Delegado | Enviar correos desde buzones compartidos |
| `MailboxSettings.Read` | Delegado / Aplicación | Leer configuración del buzón |
| `MailboxSettings.ReadWrite` | Delegado / Aplicación | Leer y escribir configuración del buzón |

### 3.2. Nuevo Permiso Avanzado — Mail-Advanced.ReadWrite (2026)

A partir del **31 de diciembre de 2026**, las aplicaciones que modifiquen propiedades sensibles en mensajes no borradores necesitarán el nuevo permiso `Mail-Advanced.ReadWrite`.

Propiedades afectadas: `subject`, `body`, `toRecipients`, `ccRecipients`, `bccRecipients`, `from`, `sender`, `replyTo`, `internetMessageId`, `singleValueExtendedProperties`, `multiValueExtendedProperties`.

| Permiso | Tipo | Descripción |
|---------|------|-------------|
| `Mail-Advanced.ReadWrite` | Delegado | Modificar propiedades sensibles en nombre del usuario |
| `Mail-Advanced.ReadWrite.All` | Aplicación | Modificar propiedades sensibles en todos los buzones |
| `Mail-Advanced.ReadWrite.Shared` | Delegado | Modificar propiedades sensibles en buzones compartidos |

**Documentos de referencia:**
- [Microsoft Graph permissions reference (Microsoft Learn)](https://learn.microsoft.com/en-us/graph/permissions-reference)
- [Graph API Breaking Change: Mail-Advanced.ReadWrite — Mike Hacker Blog](https://blog.mikehacker.net/p/graph-api-breaking-change-new-permissions-required-for-sensitive-email-properties-by-december-2026)
- [Graph API Updates to Sensitive Email Properties (Exchange Team)](https://devblogs.microsoft.com/microsoft365dev/graph-api-updates-to-sensitive-email-properties/)
- [Update message API reference (Microsoft Learn)](https://learn.microsoft.com/en-us/graph/api/message-update?view=graph-rest-1.0&tabs=http)
- [Graph Permissions Explorer — Mail.ReadBasic](https://permissions.cengizyilmaz.net/permissions/mail-readbasic.html)

---

## 4. Autenticación y Conexión

### 4.1. Conexión con Delegated Permissions (usuario autenticado)

```powershell
Connect-MgGraph -Scopes "Mail.Read", "Mail.Send"
```

### 4.2. Conexión con Application Permissions (daemon/app-only)

```powershell
# Autenticación por secret
Connect-MgGraph -TenantId $tenantID -ClientId $AzureAppID -ClientSecretCredential $credential

# Autenticación por certificado
Connect-MgGraph -TenantId $tenantID -ClientId $AzureAppID -CertificateThumbprint $thumbprint
```

### 4.3. Flujo OAuth2 manual con Invoke-RestMethod

Se puede obtener un token de acceso directamente contra el endpoint de Entra ID:

```powershell
$tokenBody = @{
    Grant_Type    = "client_credentials"
    Scope         = "https://graph.microsoft.com/.default"
    Client_Id     = $AzureAppID
    Client_Secret = $AccessSecret
}
$tokenResponse = Invoke-RestMethod -Uri "https://login.microsoftonline.com/$tenantID/oauth2/v2.0/token" -Method POST -Body $tokenBody
$headers = @{ "Authorization" = "Bearer $($tokenResponse.access_token)" }
```

**Documentos de referencia:**
- [Connecting to Microsoft Graph API using PowerShell (WOSHUB)](https://woshub.com/access-azure-microsoft-graph-api-powershell/)
- [Certificate Auth for Microsoft Graph (C7Solutions)](https://c7solutions.com/2025/07/certificate-auth-for-microsoft-graph)

---

## 5. Envío de Correos

### 5.1. Con Send-MgUserMail (Microsoft.Graph Module)

```powershell
$Message = @{
    Subject = "Hello World from GraphAPI"
    Body = @{ ContentType = "HTML"; Content = $msgBody }
    ToRecipients = @(@{ EmailAddress = @{ Address = $MailTo } })
    Attachments = @(@{
        "@odata.type" = "#microsoft.graph.fileAttachment"
        Name = "file.log"
        ContentType = "application/octet-stream"
        ContentBytes = $AttachmentBase64
    })
}
Send-MgUserMail -UserId $MailFrom -Message $Message
```

### 5.2. Con Invoke-RestMethod (REST API directa)

```powershell
$URLsend = "https://graph.microsoft.com/v1.0/users/$MailFrom/sendMail"
Invoke-RestMethod -Method POST -Uri $URLsend -Headers $headers -Body $BodyJsonsend
```

**Documentos de referencia:**
- [Send Emails with Microsoft Graph API and PowerShell (WOSHUB)](https://woshub.com/send-email-microsoft-graph-api-powershell/)
- [Send email using Microsoft Graph Mailer (WPO365)](https://docs.wpo365.com/article/141-send-email-using-microsoft-graph-mailer)

---

## 6. Restricción de Acceso a Buzones

### 6.1. Application Access Policy (Exchange Online — heredado)

```powershell
New-ApplicationAccessPolicy -AppId "xxxx-xxxx" -PolicyScopeGroupId azappSendasAllowed -AccessRight RestrictAccess
```

### 6.2. RBAC for Applications en Exchange Online (reemplazo moderno)

```powershell
New-ServicePrincipal -AppID $AppID -ObjectID $EnterpriseAppObjectID -DisplayName "AppName RBAC"
New-ManagementScope -Name "rbac_$AppID" -RecipientRestrictionFilter "GUID -eq '$($TargetMailbox.GUID)'"
New-ManagementRoleAssignment -App $AppID -Role "Application Mail.ReadWrite" -CustomResourceScope "rbac_$AppID"
```

Roles disponibles para Service Principal: `Application Mail.Read`, `Application Mail.ReadWrite`, `Application Mail.Send`, entre otros (14 roles en total).

**Documentos de referencia:**
- [Secure Access to Mailboxes via Graph — Brian Reid (C7Solutions)](https://c7solutions.com/2024/09/secure-access-to-mailboxes-via-graph)
- [Configure API permissions (Microsoft Learn — Intranet Connections)](https://support.intranetconnections.com/hc/en-us/articles/37979916803223-Microsoft-Graph-Mail-Configuration-and-Admin-Controls)

---

## 7. Consideraciones sobre Límites y Throttling

### 7.1. Límites de tamaño de adjuntos
- Adjuntos < 3 MB: POST directo a `attachments` navigation property
- Adjuntos entre 3 MB y 150 MB: uso de `New-MgUserMessageAttachmentUploadSession` (carga por rangos)
- Límite combinado: 150 MB por mensaje (incluyendo todas las partes)

### 7.2. Throttling
- La API limita por `IncomingBytes` (cantidad de datos subidos en 5 minutos)
- 150 MB por combinación app + mailbox cada 5 minutos

**Documentos de referencia:**
- [Throttling limits (Microsoft Learn)](https://learn.microsoft.com/en-us/graph/throttling-limits)
- [When sending emails > 150 MB (Microsoft Q&A)](https://learn.microsoft.com/en-us/answers/questions/1730503/when-sending-emails-using-microsoft-graph-api-what)

---

## 8. Casos de Uso Prácticos

| Caso de Uso | Descripción | Cmdlets Clave |
|-------------|-------------|---------------|
| Archivado automatizado de correos | Exportar mensajes a .eml para cumplimiento legal | `Get-MgUserMessageContent`, `Get-MgUserMessage` |
| Investigación forense | Recuperar contenido completo de mensajes sospechosos | `Get-MgUserMessageContent` + `-OutFile` |
| Auditoría de Elementos eliminados | Listar y exportar correos eliminados | `Get-MgUserMailFolder` + `Get-MgUserMailFolderMessage` |
| Envío masivo de notificaciones | Enviar correos HTML con adjuntos desde scripts | `Send-MgUserMail` |
| Sincronización incremental | Mantener una copia local sincronizada de los mensajes | `Get-MgUserMessageDelta` |
| Reglas de bandeja de entrada | Automatizar organización del correo entrante | `New-MgUserMailFolderMessageRule` |

**Documentos de referencia:**
- [Filter Email Messages with Microsoft Graph API](https://usercomp.com/news/1400766/filter-emails-with-microsoft-graph-api)

---

## 9. Referencias Cruzadas y Recursos Adicionales

### 9.1. Documentación Oficial de Microsoft
- [Microsoft.Graph.Mail Module (Microsoft Learn)](https://learn.microsoft.com/en-us/powershell/module/microsoft.graph.mail/?view=graph-powershell-1.0)
- [Microsoft Graph permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference)
- [Outlook mail API overview](https://learn.microsoft.com/en-us/graph/outlook-mail-concept-overview)
- [Microsoft Graph PowerShell Overview](https://docs.microsoft.com/en-us/powershell/microsoftgraph/)
- [Microsoft Graph API Overview](https://docs.microsoft.com/en-us/graph/api/overview)

### 9.2. Artículos y Tutoriales
- [Send Emails with Microsoft Graph API and PowerShell — WOSHUB](https://woshub.com/send-email-microsoft-graph-api-powershell/)
- [Get-MgUserMessageContent — M365 Corner](https://m365corner.com/m365-powershell/using-get-mgusermessagecontent-in-graph-powershell.html)
- [Retrieve Emails from Deleted Items Folder — M365 Corner](https://m365corner.com/m365-powershell/retrieve-emails-from-deleted-items-folder.html)
- [Secure Access to Mailboxes via Graph — Brian Reid / C7Solutions](https://c7solutions.com/2024/09/secure-access-to-mailboxes-via-graph)
- [Graph API Breaking Change (Mail-Advanced.ReadWrite) — Mike Hacker](https://blog.mikehacker.net/p/graph-api-breaking-change-new-permissions-required-for-sensitive-email-properties-by-december-2026)
- [Filter Email Messages with Microsoft Graph API](https://usercomp.com/news/1400766/filter-emails-with-microsoft-graph-api)
- [Microsoft Graph Mail Configuration — Intranet Connections](https://support.intranetconnections.com/hc/en-us/articles/37979916803223-Microsoft-Graph-Mail-Configuration-and-Admin-Controls)

### 9.3. Herramientas
- [Graph Permissions Explorer](https://permissions.cengizyilmaz.net/permissions/mail-readbasic.html) — Explorador interactivo de permisos de Graph
- [PowerShell Gallery — Microsoft.Graph.Mail](https://www.powershellgallery.com/packages/Microsoft.Graph.Mail/) — Descarga del módulo
- [Cmdlet Finder — M365 Corner](https://m365corner.com/graph-cmdlet-finder.html) — Buscador de cmdlets de Graph PowerShell
