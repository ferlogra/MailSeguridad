#requires -Version 5.1
<#
.SYNOPSIS
Genera un Excel de tickets (INC/CS/CRQ/SOAR) a partir de correos de Outlook en la carpeta Bandeja de entrada.

.DESCRIPTION
Consulta mensajes de la carpeta "Bandeja de entrada" (o una carpeta indicada) mediante Microsoft Graph PowerShell,
aplica filtros configurables (Include/Exclude con l�gica AND/OR y condiciones sobre From/Subject/Body),
extrae IDs principales por patr�n (INC/CS/CRQ), agrupa por ID principal, detecta estados y relaciones,
y exporta el resultado a Excel usando una plantilla.

No descarga correos ni adjuntos; solo consulta metadatos y contenido textual necesario para el an�lisis.

Incluye verificaci�n e instalaci�n autom�tica de dependencias:
- Microsoft.Graph.Authentication
- Microsoft.Graph.Mail
- ImportExcel
- PSSQLite

.PARAMETER UserId
UPN o identificador del buz�n a consultar.
Ejemplo: fernando.lopez@tirea.es

.PARAMETER DaysBack
N�mero de d��as hacia atr�s a consultar desde el momento actual.
Por defecto 60.

.PARAMETER MailFolderName
Nombre de la carpeta de correo a consultar.
Por defecto "Bandeja de entrada".

.PARAMETER MailFolderNameMove
Nombre de la carpeta de correos filtrados a dejar.
Por defecto "", no mueve los correos.

.PARAMETER TemplatePath
Ruta a la plantilla Excel .xlsx.
Por defecto: .\tickets_telefonica.xlsx

.PARAMETER WorksheetName
Nombre de la hoja del Excel donde se escribir� la salida.
Por defecto: Tickets

.PARAMETER OutputPath
Ruta del Excel de salida.
Si no se indica, se genera como tickets_telefonica_YYYYMMDD.xlsx en el directorio actual.

.PARAMETER InstallDependencies
Si se indica, intentar� instalar autom�ticamente m�dulos faltantes desde PowerShell Gallery.

.PARAMETER Scope
Ámbito de instalaci�n de m�dulos si falta alguna dependencia.
Valores v�lidos: CurrentUser, AllUsers
Por defecto: CurrentUser

.PARAMETER ForceRecreateOutput
Si se indica y ya existe el archivo de salida, lo sobrescribe.

.PARAMETER VerboseLogging
Muestra m�s detalle en pantalla.

.PARAMETER MaxMessages
Límite de mensajes a leer desde la carpeta. Por defecto 2000.
Útil para controlar duración/coste de la consulta.

.PARAMETER UseGraphWebLinkOnly
Si se indica, solo utiliza la propiedad webLink devuelta por Graph para el enlace a Outlook.
Si no se indica, cuando webLink venga vacío intentará construir un deeplink OWA de compatibilidad.

.PARAMETER outBBDD
Ruta a la base de datos SQLite donde exportar los mensajes filtrados.
Si se indica, los mensajes se guardan en la tabla "Mensajes" de la BBDD especificada,
con los mismos campos que la salida Excel m�s el campo Revision.
Ejemplo: C:\Datos\tickets.db

.EXAMPLE
.\Export-OutlookTicketReport.ps1 -UserId "fernando.lopez@tirea.es" -InstallDependencies -VerboseLogging

Conecta a Microsoft Graph, consulta los �ltimos 60 d��as en Bandeja de entrada, aplica filtros,
y genera el Excel de salida usando la plantilla tickets_telefonica.xlsx.

.EXAMPLE
.\Export-OutlookTicketReport.ps1 -UserId "fernando.lopez@tirea.es" -outBBDD "C:\Datos\tickets.db" -InstallDependencies

Conecta a Microsoft Graph, consulta los �ltimos 60 d��as en Bandeja de entrada, aplica filtros,
y exporta el resultado a la base de datos SQLite C:\Datos\tickets.db (tabla Mensajes),
adem�s de generar el Excel de salida.

.EXAMPLE
.\Export-OutlookTicketReport.ps1 `
  -UserId "fernando.lopez@tirea.es" `
  -DaysBack 45 `
  -TemplatePath "C:\Informes\tickets_telefonica.xlsx" `
  -OutputPath "C:\Informes\tickets_telefonica_$(Get-Date -Format yyyyMMdd).xlsx" `
  -InstallDependencies `
  -ForceRecreateOutput

Genera el Excel en una ruta concreta sobrescribiendo si ya existe.

.EXAMPLE
Get-Help .\Export-OutlookTicketReport.ps1 -Detailed

Muestra la ayuda detallada del script.

.NOTES
Requisitos funcionales:
- Permisos delegados de Microsoft Graph para leer correo del buz�n consultado.
- Se recomienda Mail.Read. En algunos escenarios básicos puede bastar Mail.ReadBasic,
  pero para leer cuerpo/asunto/webLink y aplicar reglas de contenido suele ser preferible Mail.Read.

La exportaci�n Excel usa ImportExcel, que permite crear .xlsx sin requerir Excel instalado.

#>

[CmdletBinding()]
param(
    [string]$UserId,

    [Parameter()]
    [ValidateRange(1,3650)]
    [int]$DaysBack = 60,

    [Parameter()]
    [string]$MailFolderName = "Bandeja de entrada",

    [Parameter()]
    [string]$MailFolderNameMove = "",

    [Parameter()]
    [string]$TemplatePath = "C:\ps1\tickets_telefonica.xlsx",

    [Parameter()]
    [string]$WorksheetName = "Tickets",

    [Parameter()]
    [string]$OutputPath = "C:\ps1\",

    [Parameter()]
    [switch]$InstallDependencies,

    [Parameter()]
    [ValidateSet("CurrentUser","AllUsers")]
    [string]$Scope = "CurrentUser",

    [Parameter()]
    [switch]$ForceRecreateOutput,

    [Parameter()]
    [switch]$VerboseLogging,

    [Parameter()]
    [ValidateRange(1,50000)]
    [int]$MaxMessages = 2000,

    [Parameter()]
    [switch]$UseGraphWebLinkOnly,

    [Parameter()]
    [string]$outBBDD
)

begin {
    
# param(
#     [datetime]$fechaInicio
# )

    $version= "1.9"

    function Write-Log {
        param(
            [string]$Message,
            [ValidateSet("INFO","WARN","ERROR","DEBUG")]
            [string]$Level = "INFO"
        )
        $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        if ($Level -eq "DEBUG" -and -not $VerboseLogging) { return }

        switch ($Level) {
            "INFO"  { Write-Host "[$ts] [INFO ] $Message" -ForegroundColor Cyan }
            "WARN"  { Write-Host "[$ts] [WARN ] $Message" -ForegroundColor Yellow }
            "ERROR" { Write-Host "[$ts] [ERROR] $Message" -ForegroundColor Red }
            "DEBUG" { Write-Host "[$ts] [DEBUG] $Message" -ForegroundColor DarkGray }
        }
    }

    function Ensure-PackageProviderNuGet {
            [CmdletBinding()]
            param()

            try {
                $provider = Get-PackageProvider -Name NuGet -ErrorAction SilentlyContinue
                if (-not $provider) {
                    Write-Log "No se encontr� el proveedor NuGet. Intentando instalarlo..." "WARN"
                    Install-PackageProvider -Name NuGet -Force -Scope CurrentUser | Out-Null
                }
            }
            catch {
                Write-Log "No se pudo instalar/verificar el proveedor NuGet: $($_.Exception.Message)" "ERROR"
                throw
            }
        }


    function Expand-GzipFile {
        param (
            [string]$Source
        )

        $destination = $Source -replace '\.gz$',''

        $input = [System.IO.FileStream]::new($Source, [IO.FileMode]::Open, [IO.FileAccess]::Read)
        $output = [System.IO.FileStream]::new($destination, [IO.FileMode]::Create, [IO.FileAccess]::Write)
        $gzip = [System.IO.Compression.GzipStream]::new($input, [IO.Compression.CompressionMode]::Decompress)

        $buffer = New-Object byte[] 8192

        while (($read = $gzip.Read($buffer, 0, $buffer.Length)) -gt 0) {
            $output.Write($buffer, 0, $read)
        }

        $gzip.Close()
        $output.Close()
        $input.Close()
    }

    function Ensure-Module {
        [CmdletBinding()]
        param(
            [Parameter(Mandatory)]
            [string]$Name,

            [string]$MinimumVersion = "",

            [switch]$TryInstall,

            [ValidateSet("CurrentUser","AllUsers")]
            [string]$InstallScope = "CurrentUser"
        )

        $module = Get-Module -ListAvailable -Name $Name |
                  Sort-Object Version -Descending |
                  Select-Object -First 1

        $ok = $false
        if ($module) {
            if ([string]::IsNullOrWhiteSpace($MinimumVersion)) {
                $ok = $true
            }
            else {
                try {
                    $ok = ([version]$module.Version -ge [version]$MinimumVersion)
                }
                catch {
                    $ok = $false
                }
            }
        }

        if (-not $ok) {
            if (-not $TryInstall) {
                throw "Falta el módulo '$($Name)' o no cumple versión mínima. Usa -InstallDependencies para intentar instalarlo."
            }

            Ensure-PackageProviderNuGet

            Write-Log "Instalando módulo '$($Name)'..." "WARN"
            $params = @{
                Name         = $Name
                Scope        = $InstallScope
                Force        = $true
                AllowClobber = $true
            }
            if (-not [string]::IsNullOrWhiteSpace($MinimumVersion)) {
                $params.MinimumVersion = $MinimumVersion
            }

            Install-Module @params
        }

        Import-Module $Name -ErrorAction Stop
        Write-Log "Módulo cargado: $($Name)" "DEBUG"
    }

    function Resolve-MailFolderId {
        [CmdletBinding()]
        param(
            [Parameter(Mandatory)] [string]$UserId,
            [Parameter(Mandatory)] [string]$FolderName
        )

        Write-Log "Buscando carpeta '$FolderName' en el buzón $UserId..." "INFO"

        $folders = Get-MgUserMailFolder -UserId $UserId -All
        $folder = $folders | Where-Object { $_.DisplayName -eq $FolderName } | Select-Object -First 1

        if (-not $folder) {
            throw "No se encontró la carpeta '$FolderName' en el buzn '$UserId'."
        }

        return $folder.Id
    }


    function Find-MailFolderRecursive {
        param(
            [string]$UserId,
            [string]$ParentFolderId,
            [string]$FolderName
        )

        # Obtener subcarpetas del nivel actual
        $childFolders = Get-MgUserMailFolderChildFolder `
            -UserId $UserId `
            -MailFolderId $ParentFolderId `
            -All

        foreach ($folder in $childFolders) {

            Write-log "Comprobando: $($folder.DisplayName)" "DEBUG"

            # ¿Es la carpeta buscada?
            if ($folder.DisplayName -eq $FolderName) {
                return $folder
            }

            # Buscar recursivamente en las subcarpetas
            $result = Find-MailFolderRecursive `
                -UserId $UserId `
                -ParentFolderId $folder.Id `
                -FolderName $FolderName

            if ($null -ne $result) {
                return $result
            }
        }

        return $null
    }


    function Test-Condition {
        [CmdletBinding()]
        param(
            [Parameter(Mandatory)] $Mail,
            [Parameter(Mandatory)] [hashtable]$Condition
        )

        # if( $Condition.GetType() -ne [Hashtable] ) {
        if( $Condition.ContainsKey('Type') ) {
            $fieldValue = switch ($Condition.Field) {
                "From"    { $Mail.From } #{ $Mail.SenderEmailAddress }
                "Domain"  { if ($Mail.SenderEmailAddress -match '@(.+)$') { $Matches[1] } else { "" } }
                "Subject" { $Mail.Subject }
                "Body"    { $Mail.Body }
                "Folder"  { $Mail.FolderName }
                default   { "" }
            }

            $condValue = [string]$Condition.Value
            Write-Log "Comprobando condicion $($Condition.Field) $($Condition.Type) $condValue" "DEBUG"
            switch ($Condition.Type) {
                "Contains"    { return ($fieldValue -like "*$condValue*") }
                "NotContains" { return ($fieldValue -notlike "*$condValue*") }
                "Equals"      { return ([string]$fieldValue -eq $condValue) }
                "NotEquals"   { return ([string]$fieldValue -ne $condValue) }
                "Regex"       { return ([regex]::IsMatch([string]$fieldValue, $condValue, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) }
                "NotRegex"    { return (-not [regex]::IsMatch([string]$fieldValue, $condValue, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) }
                default {
                    throw "Tipo de condici�n no soportado: $($Condition.Type)"
                }
            }
        } else {
            Write-Log "Preparando subfiltro" "DEBUG"
            $filtro = @{
                Conditions = $Condition.Conditions
                Name = "Subfiltro"
                Logic = $Condition.Logic
                Mode = "Include"
                Grupo = ""
            }
            $Fil2 = ""
            $Group2 = ""
            $ret = Test-Filter -Mail $Mail -Filter $filtro -Fil2 ([ref]$Fil2) -Group2 ([ref]$Group2)
            Write-Log "Resultado subfiltro $ret" "DEBUG"
            return $ret
        }
    }


    function Test-Filter {
        param($Mail, $Filter, [ref]$Fil2, [ref]$Group2)

        $results = @()
        if ( -not ( $Fil2 -is [System.Management.Automation.PSReference] ) ) {
            Write-Log "Parametro $Fil2 no es por referencia: $($_.Exception.Message)" "ERROR"                    
        }
        # $Group = ""
        Write-Log "Comprobando filtro $($Filter.Name)" "DEBUG"
        foreach ($cond in $Filter.Conditions) {
            Write-Log "Comprobando condicion $($cond.Field)" "DEBUG"
            $res = (Test-Condition -Mail $Mail -Condition $cond)
            Write-Log "Comprobada condicion $($cond.Field): $res" "DEBUG"
            if( $res ) {
                try {
                    $Fil2.Value = $Filter.Name
                    $Group2.Value = $Filter.Grupo
                } catch {
                    Write-Log "Error asignando grupo/filtro: $($_.Exception.Message)" "ERROR"                    
                }
            }
            $results += ($res)
        }

        if ($Filter.Logic -eq "AND") {
            return ($results -notcontains $false)
        } elseif ($Filter.Logic -eq "OR") {
            return ($results -contains $true)
        }
    }

    function Apply-Filters {
        param($Mail, $Filters, [ref]$Fil1, [ref]$Grupo1)

        $include = $false
        if ( -not ( $Fil1 -is [System.Management.Automation.PSReference] ) ) {
            Write-Log "Parametro $Fil1 no es por referencia: $($_.Exception.Message)" "ERROR"                    
        }
        # $Grupo.Value = ""
        foreach ($filter in $Filters) {

            if( $filter.name -eq "Tirea" ) {
                Write-log "" "DEBUG"
            }
            Write-Log "Comprobando filtro $($filter.Name)" "DEBUG"
            $match = Test-Filter -Mail $Mail -Filter $filter -Fil2 $Fil1 -Group2 $Grupo1
            Write-Log "Comprobado filtro $($filter.Name): $match" "DEBUG"
            if ($filter.Mode -eq "Exclude" -and $match) {
                return $true
            }

            if ($filter.Mode -eq "Include" -and $match) {
                return $false
            }
        }

        return $true  # por defecto incluir si no se excluye
    }

    function Normalize-Message {
        [CmdletBinding()]
        param(
            [Parameter(Mandatory)] $Message,
            [Parameter(Mandatory)] [string]$FolderDisplayName,
            [Parameter(Mandatory)] [string]$Revision
        )

        $fromAddress = $null
        $fromName    = $null

        if ($Message.From -and $Message.From.EmailAddress) {
            $fromAddress = $Message.From.EmailAddress.Address
            $fromName    = $Message.From.EmailAddress.Name
        }
        elseif ($Message.Sender -and $Message.Sender.EmailAddress) {
            $fromAddress = $Message.Sender.EmailAddress.Address
            $fromName    = $Message.Sender.EmailAddress.Name
        }
        elseif ($Message.SenderEmailAddress -and $Message.SenderName) {
            $fromAddress = $Message.SenderEmailAddress
            $fromName    = $Message.SenderName
        }
       

        $bodyText = ""
        if ($Message.Body -and $Message.Body.Content) {
            $bodyText = $Message.Body.Content
        }
        elseif ($Message.BodyPreview) {
            $bodyText = $Message.BodyPreview
        }
        elseif ($Message.Body) {
            $bodyText = $Message.Body
        }

        # Limpieza ligera de HTML básica si viniese contenido HTML
        $bodyText = $bodyText -replace '<[^>]+>', ' '
        $bodyText = $bodyText -replace '\s+', ' '

        if( -not ($Message.Id) ) {
           $Id = $Message.EntryID
        } else {
           $Id = $Message.Id
        }


        $outlookUrl = ""
        if ($Message.WebLink) {
            $outlookUrl = $Message.WebLink
        }
        elseif (-not $UseGraphWebLinkOnly -and $Message.Id) {
            # Fallback pr�ctico si Graph no devuelve webLink.
            # No se garantiza que sobreviva a movimientos entre carpetas.
            $encodedId = [System.Uri]::EscapeDataString($Id)
            $outlookUrl = "https://outlook.office.com/mail/deeplink/read/$encodedId?ItemID=$encodedId&exvsurl=1"
        }
        if( $Message.ReceivedDateTime ) {
            $Received = $Message.ReceivedDateTime
        } else {
            $Received = $Message.ReceivedTime
        }
        $grupo = ""
        $filtro = ""

        # Destinatarios To
        $toList = @()
        if ($Message.ToRecipients) {
            foreach ($r in $Message.ToRecipients) {
                $addr = if ($r.EmailAddress -and $r.EmailAddress.Address) { $r.EmailAddress.Address } else { "" }
                $name = if ($r.EmailAddress -and $r.EmailAddress.Name) { $r.EmailAddress.Name } else { "" }
                if ($name -and $addr) { $toList += "$name <$addr>" }
                elseif ($addr)       { $toList += $addr }
            }
        }
        $toStr = $toList -join "; "

        # Destinatarios CC
        $ccList = @()
        if ($Message.CcRecipients) {
            foreach ($r in $Message.CcRecipients) {
                $addr = if ($r.EmailAddress -and $r.EmailAddress.Address) { $r.EmailAddress.Address } else { "" }
                $name = if ($r.EmailAddress -and $r.EmailAddress.Name) { $r.EmailAddress.Name } else { "" }
                if ($name -and $addr) { $ccList += "$name <$addr>" }
                elseif ($addr)       { $ccList += $addr }
            }
        }
        $ccStr = $ccList -join "; "

        # ¿El cuerpo del mensaje es HTML?
        $isHtml = $false
        if ($Message.Body -and $Message.Body.ContentType) {
            $isHtml = ($Message.Body.ContentType -eq "HTML")
        }

        [pscustomobject]@{
            Id                = [string]$Message.Id
            MessageId         = [string]$Id
            InternetMessageId = [string]$Message.InternetMessageId
            ConversationId    = [string]$Message.ConversationId
            Subject           = [string]$Message.Subject
            ReceivedDateTime  = [datetime]$Received
            SentDateTime      = if ($Message.SentDateTime) { [datetime]$Message.SentDateTime } else { $null }
            From              = [string]$fromAddress
            FromName          = [string]$fromName
            To                = $toStr
            Cc                = $ccStr
            Body              = [string]$bodyText
            IsBodyHTML        = $isHtml
            FolderName        = [string]$FolderDisplayName
            ParentFolderId    = [string]$Message.ParentFolderId
            OutlookUrl        = [string]$outlookUrl
            Grupo             = [string]$grupo
            Filtro            = [string]$filtro
            Revision          = [string]$Revision
        }
    }

    function Connect-GraphIfNeeded {
        [CmdletBinding()]
        param()

        try {
            $ctx = Get-MgContext -ErrorAction SilentlyContinue
            if ($ctx) {
                if ($ctx.Scopes -notcontains "Mail.ReadWrite") {
                    Write-Log "No dispone permiso 'Mail.ReadWrite'. Reconectando" "INFO"
                    Disconnect-MgGraph
                    $ctx = $null
                }
                if ($ctx.Scopes -notcontains "User.Read") {
                    Write-Log "No dispone permiso 'User.Read'. Reconectando" "INFO"
                    Disconnect-MgGraph
                    $ctx = $null                    
                }
            }
            if (-not $ctx) {
                Write-Log "Conectando a Microsoft Graph..." "INFO"
                $ctx =Connect-MgGraph -Scopes @(
                    "Mail.Read",
                    "Mail.ReadBasic",
                    "User.Read",
                    "Mail.ReadWrite"
                ) -NoWelcome | Out-Null
                if( -not $ctx ) {
                    throw "No se pudo conectar a Microsoft Graph. Verifique permisos y autenticaci�n."
                }
            }
            else {
                Write-Log "Ya existe una sesi�n activa de Microsoft Graph." "INFO"
            }

         if ($ctx.Scopes -notcontains "Mail.ReadWrite") {
                Write-Log "No dispone permiso 'Mail.ReadWrite'" "ERROR"
                throw
            }
            if ($ctx.Scopes -notcontains "User.Read") {
                Write-Log "No dispone permiso 'User.Read'" "ERROR"
                throw
            }
            

            # Select-MgProfile -Name "v2.X" | Out-Null
            # Get-MgUser  -UserId| Out-Null
        }
        catch {
            Write-Log "Error al conectar con Microsoft Graph: $($_.Exception.Message)" "ERROR"
            throw
        }
    }
    function Get-MailMessagesFromFolder {
        [CmdletBinding()]
        param(
            [Parameter(Mandatory)] [string]$UserId,
            [Parameter(Mandatory)] [string]$MailFolderId,
            [Parameter(Mandatory)] [datetime]$ReceivedAfter,
            [int]$Top = 2000
        )

        # Propiedades necesarias para an�lisis
        $properties = @(
            "id",
            "internetMessageId",
            "subject",
            "receivedDateTime",
            "sentDateTime",
            "from",
            "sender",
            "bodyPreview",
            "body",
            "parentFolderId",
            "conversationId",
            "conversationIndex",
            "webLink",
            "isRead"
        )

        $graphDate = $ReceivedAfter.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        $filter = "receivedDateTime ge $graphDate"

        Write-Log "Leyendo mensajes desde la carpeta ($MailFolderId) con filtro: $filter" "INFO"

        $msgs = Get-MgUserMailFolderMessage `
            -UserId $UserId `
            -MailFolderId $MailFolderId `
            -All `
            -PageSize 200 `
            -Top $Top `
            -Property $properties `
            -Filter $filter

        # Ordenar respuesta por orden descendente
        $msgs = $msgs | Sort-Object ReceivedDateTime -Descending
        return @($msgs)
    }

    function Get-AllIdsFromText {
        [CmdletBinding()]
        param([string]$Text)

        if ([string]::IsNullOrWhiteSpace($Text)) {
            return @()
        }
        $rx = [regex]'(?i)\b(INC\d+|CS\d+|CRQ\d+|Ticket\#\d+|Case\ \#\d+|CVE\-\d+\-\d+|sonatype\-\d+\-\d+|.+\[\D+\ \#\d+\].+)\b'
        $ms = $rx.Matches($Text)
        return $ms | ForEach-Object { $_.Value.ToUpper() } | Select-Object -Unique
    }

    function Get-PrimaryId {
        [CmdletBinding()]
        param(
            [string]$Subject,
            [string]$Body
        )

        $ids = @()
        $ids += Get-AllIdsFromText -Text $Subject
        $subjectIds = $ids
        $ids += Get-AllIdsFromText -Text $Body
        $ids  = $ids | Select-Object -Unique

        if (-not $ids -or $ids.Count -eq 0) { return $null }



        # Prioridad: primero por aparici�n en el asunto; si no, por orden INC/CS/CRQ o el primero encontrado
        # $subjectIds = Get-AllIdsFromText -Text $Subject
        if ($subjectIds.Count -gt 0) {
            return $subjectIds[0].ToUpper()
        }

        if ( $ids -is [string] ) {
            return $ids.ToUpper()
        }
        return $ids[0].ToUpper()
    }

    function Get-FamilyFromId {
        [CmdletBinding()]
        param([string]$Id)

        if (-not $Id) { return "" }

        if ($Id -like "INC*") { return "INC" }
        if ($Id -like "CS*")  { return "CS"  }
        if ($Id -like "CRQ*") { return "CRQ" }
        if ($id -like "TICKET*") { return "TICKET" }
        if ($id -like "CASE*") { return "CASE" }
        if ($id -like "CVE*") { return "CVE" }
        if ($id -like "SONATYPE*") { return "SONATYPE" }
        if ($id -match "\[(.+?)\s+\#(\d+)\]") { return "RT" }
        return ""
    }

    function Get-RelatedIds {
        [CmdletBinding()]
        param(
            [string]$PrimaryId,
            [array]$Messages
        )

        $text = (($Messages | ForEach-Object { $_.Subject; $_.Body }) -join " ")
        $ids = Get-AllIdsFromText -Text $text | Where-Object { $_ -ne $PrimaryId }

        [pscustomobject]@{
            INC = ($ids | Where-Object { $_ -like "INC*" } | Select-Object -Unique) -join "; "
            CS  = ($ids | Where-Object { $_ -like "CS*"  } | Select-Object -Unique) -join "; "
            CRQ = ($ids | Where-Object { $_ -like "CRQ*" } | Select-Object -Unique) -join "; "
            TICKET = ($ids | Where-Object { $_ -like "TICKET*" } | Select-Object -Unique) -join "; "
            CASE = ($ids | Where-Object { $_ -like "CASE*" } | Select-Object -Unique) -join "; "
            CVE = ($ids | Where-Object { $_ -like "CVE*" } | Select-Object -Unique) -join "; "
            SONATYPE = ($ids | Where-Object { $_ -like "SONATYPE*" } | Select-Object -Unique) -join "; "
            RT = ($ids | Where-Object { $_ -match "\[(.+?)\s+\#(\d+)\]" } | Select-Object -Unique) -join "; "
        }
    }

    function Get-StateFromThread {
        [CmdletBinding()]
        param(
            [Parameter(Mandatory)] [string]$PrimaryId,
            [Parameter(Mandatory)] [string]$Family,
            [Parameter(Mandatory)] [array]$Messages,
            [switch]$IsSoar
        )

        $fullText = (($Messages | ForEach-Object { $_.Subject; $_.Body }) -join " ")

        if ($IsSoar) {
            if ($fullText -match '\bInProgress\b') { return "en proceso" }
            if ($fullText -match '\bOpen\b')       { return "pendiente" }
            if ($fullText -match '\bClosed\b|\bResolved\b') { return "resuelto" }
            return ""
        }

        if ($Family -eq "CRQ") {
            if ($fullText -match '(?i)\bFIN OK\b') { return "resuelto" }
        }

        if ($fullText -match '(?i)\bClosed\b|\bResolved\b|finalizado con �xito|finalizado con exito') {
            return "resuelto"
        }

        return ""
    }

    function Get-ActionType {
        [CmdletBinding()]
        param(
            [Parameter(Mandatory)] [array]$Messages,
            [switch]$IsSoar
        )

        $fullText = (($Messages | ForEach-Object { $_.Subject; $_.Body }) -join " ")

        if ($IsSoar) {
            $sensor = ""
            if ($fullText -match '(?i)soc[a-z0-9_-]+') {
                $sensor = $Matches[0]
            }

            if ($sensor) {
                return "Alerta SOAR ($sensor)"
            }
            return "Alerta SOAR"
        }

        $subject = ($Messages | Sort-Object ReceivedDateTime -Descending | Select-Object -First 1).Subject

        switch -Regex ($subject) {
            '(?i)snapshot'       { return "Snapshot" }
            '(?i)backup'         { return "Backup" }
            '(?i)fortigate'      { return "Seguridad/red" }
            '(?i)ldap|keycloak'  { return "Identidad/LDAP" }
            '(?i)parche|upgrade' { return "Parcheado/upgrade" }
            '(?i)windows'        { return "Windows" }
            '(?i)mongo'          { return "Base de datos" }
            '(?i)glassfish|jboss'{ return "Middleware" }
            '(?i)ventana'        { return "Ventana mantenimiento" }
            '(?i)New detection'  { return "Bloqueo IP" }
            default              { 
                if ( $Messages[0].From -like "*.rt@tirea.es" ) {
                    return "RT"
                } else {
                    return "Gestion ticket" 
                }
            }
        }
    }

    function Get-WindowOrDate {
        [CmdletBinding()]
        param([array]$Messages)

        $text = (($Messages | ForEach-Object { $_.Subject; $_.Body }) -join " ")

        $patterns = @(
            '(?<w>\b\d{2}:\d{2}\s*-\s*\d{2}:\d{2}\b)',
            '(?<w>\b\d{1,2}/\d{1,2}/\d{4}\b)',
            '(?<w>\bHasta\b[^.;\n\r]+)',
            '(?<w>\bPropuesto\b[^.;\n\r]+)'
        )

        foreach ($p in $patterns) {
            $m = [regex]::Match($text, $p, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
            if ($m.Success) {
                return $m.Groups["w"].Value.Trim()
            }
        }

        return ""
    }

    function Is-SoarMessage {
        [CmdletBinding()]
        param([Parameter(Mandatory)] $Mail)

        # Solo Bandeja de entrada + remitente SOAR o asunto [AC][INC
        if ($Mail.FolderName -ne "Bandeja de entrada") {
            return $false
        }

        if ($Mail.From -eq "no-reply-soar@cybersecurity.telefonica.com") {
            return $true
        }

        # if ($Mail.Subject -like "*[AC][INC") {
        if ($Mail.Subject -match ".+\[AC\]\[INC.+") {
            return $true
        }

        return $false
    }

    function Get-MailRelationed {
        [CmdletBinding()]
        param()

        # Para obtener mensajes relacionados, mensajes del remitente o de ambos


    }

    function Build-OutputRows {
        [CmdletBinding()]
        param(
            [Parameter(Mandatory)] [array]$Messages,
            [string]$UserPrincipalName = ""
        )

        $nuevo = 0
        $work = foreach ($m in $Messages) {
            # if( $m.MessageId -eq "AAMkADkxNWI4MDc3LTgzYWMtNGEzOC04MzAwLThmYWNhODIwZjEwYQBGAAAAAADlEJekpf7iTrqq0IhysK2RBwA8caBtt_rHT6eiXTWY_2ZKAAAAAAEMAAA8caBtt_rHT6eiXTWY_2ZKAAuNR8ivAAA=" ) {
            #     Write-Log "Faltan datos de ticket/caso/INC/CVE... en mensaje: $($m.MessageId)" "WARN"
            # }
            $primaryId = Get-PrimaryId -Subject $m.Subject -Body $m.Body
            $family = Get-FamilyFromId -Id $primaryId
            $isSoar = Is-SoarMessage -Mail $m

            if ($primaryId -or $isSoar) {
                [pscustomobject]@{
                    Message   = $m
                    PrimaryId = if ($primaryId) { $primaryId } else { $null }
                    Family    = if ($isSoar -and -not $primaryId) { "INC" } else { $family }
                    IsSoar    = $isSoar
                }
            } else {
                # Write-Log "Faltan datos de ticket/caso/INC/CVE... en mensaje: $($m.MessageId)" "WARN"
                Write-Log "Faltan datos de ticket/caso/INC/CVE... en mensaje de: $($m.From) con asunto: $($m.Subject) del $($m.ReceivedDateTime)" "WARN"
                $nuevo += 1
                # if ( -not ($family)) {
                #     $family = "????"
                # }
                [pscustomobject]@{
                    Message   = $m
                    PrimaryId = "????" + $nuevo.ToString()
                    Family    = "????" + $nuevo.ToString()
                    IsSoar    = $isSoar
                }
            }
        }

        # Para SOAR sin ID principal expl�cito, intentamos recuperar INC del asunto/cuerpo
        foreach ($item in $work | Where-Object { $_.IsSoar -and -not $_.PrimaryId }) {
            $ids = Get-AllIdsFromText -Text ($item.Message.Subject + " " + $item.Message.Body)
            $inc = $ids | Where-Object { $_ -like "INC*" } | Select-Object -First 1
            if ($inc) {
                $item.PrimaryId = $inc
                $item.Family = "INC"
            }
        }

        $groupable = $work | Where-Object { $_.PrimaryId }

        $groups = $groupable | Group-Object -Property PrimaryId

        Write-Log "Agrupando correos: $($groups.Count)" "INFO"

        $rows = foreach ($g in $groups) {
            $items = $g.Group
            $messages = $items | Select-Object -ExpandProperty Message
            $msgs = $g.Count
            $latest = $messages | Sort-Object ReceivedDateTime -Descending | Select-Object -First 1
            $family = ($items | Select-Object -ExpandProperty Family | Where-Object { $_ } | Select-Object -First 1)
            $isSoarThread = (($items | Where-Object { $_.IsSoar }).Count -gt 0)

            $related = Get-RelatedIds -PrimaryId $g.Name -Messages $messages
            $state = Get-StateFromThread -PrimaryId $g.Name -Family $family -Messages $messages -IsSoar:$isSoarThread
            $actionType = Get-ActionType -Messages $messages -IsSoar:$isSoarThread
            $window = Get-WindowOrDate -Messages $messages

            # Asunto resumen = asunto del �ltimo mensaje, sin prefijos repetidos
            $summary = $latest.Subject -replace '^(RE:|RV:|FW:|FWD:)\s*', ''
            $summary = $summary.Trim()

            # Columnas extra pedidas: lista de IDs y lista de URLs asociadas a ese registro/hilo
            $messageIds = ($messages | Sort-Object ReceivedDateTime | ForEach-Object { $_.MessageId } | Select-Object -Unique) -join "; "
            $outlookUrls = ($messages | Sort-Object ReceivedDateTime | ForEach-Object { $_.OutlookUrl } | Where-Object { $_ } | Select-Object -Unique) -join "`n"

            if ( $g.Name -match "CVE\-.+" ) {
                $id = '=HYPERLINK("https://www.cve.org/CVERecord?id=' + $g.name + '","' + $g.name + '")'
            } else {
                $id = $g.name
            }
            if ( $family -eq "RT" ) {
                if ($id -match '\[(.+?)\s+#(\d+)\]') {
                    $servicio = $matches[1]
                    $num      = [int]$matches[2]
                }
                if( $servicio -and $num ) {
                    $familia = "RT>" + $servicio
                    $newid = "[" + $servicio + " #" + $num.ToString() + "]"
                    $id = '=HYPERLINK("https://rt.ral.tirea.es/rt/Ticket/Display.html?id=' + $num.ToString() + '","' + $newid + '")'
                } else {
                    $familia = $family
                }
            } else {
                $familia = $family
            }
            [pscustomobject]@{
                Familia            = $familia
                ID_principal       = $id
                Grupo              = $latest.Grupo
                Filtro             = $latest.Filtro
                Asunto_resumen     = $summary
                Estado             = $state
                Accion_tipo        = $actionType
                INC_relacionado    = $related.INC
                CS_relacionado     = $related.CS
                CRQ_asociado       = $related.CRQ
                Ventana_o_fecha    = $window
                Ultimo_email_2026  = $latest.ReceivedDateTime.ToString("dd/MM/yyyy HH:mm")
                Remitente_ultimo   = if ($latest.FromName -and $latest.FromName.Contains('@') ) { $latest.FromName } else { $latest.From }
                Num_Mensajes       = $msgs
                MessageIds         = $messageIds
                OutlookUrls        = $outlookUrls
                Body               = [string]$latest.Body
                IsBodyHTML         = $latest.IsBodyHTML
                To                 = $latest.To
                Cc                 = $latest.Cc
                User               = $UserPrincipalName
            }
        }

        return $rows | Sort-Object {
            [datetime]::ParseExact($_.Ultimo_email_2026, "dd/MM/yyyy HH:mm", $null)
        } -Descending
    }

    function Export-ResultExcel {
        [CmdletBinding()]
        param(
            [Parameter(Mandatory)] [array]$Rows,
            [Parameter(Mandatory)] [string]$TemplatePath,
            [Parameter(Mandatory)] [string]$OutputPath,
            [Parameter(Mandatory)] [string]$WorksheetName,
            [bool]$Overwrite
        )

        if ([string]::IsNullOrWhiteSpace($OutputPath)) {
            $OutputPath = Join-Path -Path (Get-Location) -ChildPath ("tickets_telefonica_{0}.xlsx" -f (Get-Date -Format "yyyyMMdd"))
        }

        if (Test-Path $OutputPath) {
            if ($Overwrite) {
                Remove-Item $OutputPath -Force
            }
            else {
                throw "El archivo de salida ya existe: $OutputPath. Usa -ForceRecreateOutput para sobrescribirlo."
            }
        }

        if (Test-Path $TemplatePath) {
            Write-Log "Usando plantilla Excel: $TemplatePath" "INFO"
            Copy-Item -Path $TemplatePath -Destination $OutputPath -Force
        }
        else {
            Write-Log "No se encontró la plantilla '$TemplatePath'. Se creará un libro nuevo." "WARN"
        }

        if ($Rows.Count -eq 0) {
            $Rows = @(
                [pscustomobject]@{
                    Familia            = ""
                    ID_principal       = ""
                    Asunto_resumen     = ""
                    Estado             = ""
                    Accion_tipo        = ""
                    INC_relacionado    = ""
                    CS_relacionado     = ""
                    CRQ_asociado       = ""
                    Ventana_o_fecha    = ""
                    Ultimo_email_2026  = ""
                    Remitente_ultimo   = ""
                    MessageIds         = ""
                    OutlookUrls        = ""
                    Body               = ""
                    IsBodyHTML         = $false
                    To                 = ""
                    Cc                 = ""
                    User               = ""
                }
            )
        }

        # Si el workbook ya existe se reemplaza la hoja de salida
        $Rows | Export-Excel `
            -Path $OutputPath `
            -WorksheetName $WorksheetName `
            -TableName "Tickets" `
            -TableStyle "Medium6" `
            -AutoSize `
            -AutoFilter `
            -FreezeTopRow `
            -ClearSheet

        Write-Log "Excel generado: $OutputPath" "INFO"
        return $OutputPath
    }

    function Export-ResultSqlite {
        [CmdletBinding()]
        param(
            [Parameter(Mandatory)] [array]$Rows,
            [Parameter(Mandatory)] [string]$DatabasePath
        )

        if ([string]::IsNullOrWhiteSpace($DatabasePath)) {
            throw "La ruta de la BBDD SQLite no puede estar vac�a."
        }

        # Asegurar extensi�n .db
        if ($DatabasePath -notlike '*.db') {
            $DatabasePath = $DatabasePath + '.db'
        }

        Write-Log "Exportando a BBDD SQLite: $DatabasePath" "INFO"

        # Crear tabla si no existe
        $createTable = @"
CREATE TABLE IF NOT EXISTS Mensajes (
    Id                INTEGER PRIMARY KEY AUTOINCREMENT,
    Familia           TEXT,
    ID_principal      TEXT,
    Grupo             TEXT,
    Filtro            TEXT,
    Asunto_resumen    TEXT,
    Estado            TEXT,
    Accion_tipo       TEXT,
    INC_relacionado   TEXT,
    CS_relacionado    TEXT,
    CRQ_asociado      TEXT,
    Ventana_o_fecha   TEXT,
    Ultimo_email_2026 TEXT,
    Remitente_ultimo  TEXT,
    Num_Mensajes      INTEGER,
    MessageIds        TEXT,
    OutlookUrls       TEXT,
    Revision          TEXT,
    IdActuacion       INTEGER NOT NULL DEFAULT 0,
    Body              TEXT,
    IsBodyHTML        INTEGER NOT NULL DEFAULT 0,
    To                TEXT,
    Cc                TEXT,
    User              TEXT
)
"@
        Invoke-SqliteQuery -DataSource $DatabasePath -Query $createTable

        # Los registros se añaden directamente; si la tabla ya existe los datos se acumulan entre ejecuciones
        $insertSql = @"
INSERT INTO Mensajes (
    Familia, ID_principal, Grupo, Filtro, Asunto_resumen, Estado,
    Accion_tipo, INC_relacionado, CS_relacionado, CRQ_asociado,
    Ventana_o_fecha, Ultimo_email_2026, Remitente_ultimo,
    Num_Mensajes, MessageIds, OutlookUrls, Revision, IdActuacion,
    Body, IsBodyHTML, To, Cc, User
) VALUES (
    @Familia, @ID_principal, @Grupo, @Filtro, @Asunto_resumen, @Estado,
    @Accion_tipo, @INC_relacionado, @CS_relacionado, @CRQ_asociado,
    @Ventana_o_fecha, @Ultimo_email_2026, @Remitente_ultimo,
    @Num_Mensajes, @MessageIds, @OutlookUrls, @Revision, @IdActuacion,
    @Body, @IsBodyHTML, @To, @Cc, @User
)
"@

        $count = 0
        foreach ($row in $Rows) {
            Invoke-SqliteQuery -DataSource $DatabasePath -Query $insertSql -SqlParameters @{
                Familia         = if ($row.Familia)         { [string]$row.Familia }         else { '' }
                ID_principal    = if ($row.ID_principal)    { [string]$row.ID_principal }    else { '' }
                Grupo           = if ($row.Grupo)           { [string]$row.Grupo }           else { '' }
                Filtro          = if ($row.Filtro)          { [string]$row.Filtro }          else { '' }
                Asunto_resumen  = if ($row.Asunto_resumen)  { [string]$row.Asunto_resumen }  else { '' }
                Estado          = if ($row.Estado)          { [string]$row.Estado }          else { '' }
                Accion_tipo     = if ($row.Accion_tipo)     { [string]$row.Accion_tipo }     else { '' }
                INC_relacionado = if ($row.INC_relacionado) { [string]$row.INC_relacionado } else { '' }
                CS_relacionado  = if ($row.CS_relacionado)  { [string]$row.CS_relacionado }  else { '' }
                CRQ_asociado    = if ($row.CRQ_asociado)    { [string]$row.CRQ_asociado }    else { '' }
                Ventana_o_fecha = if ($row.Ventana_o_fecha) { [string]$row.Ventana_o_fecha } else { '' }
                Ultimo_email_2026 = if ($row.Ultimo_email_2026) { [string]$row.Ultimo_email_2026 } else { '' }
                Remitente_ultimo = if ($row.Remitente_ultimo) { [string]$row.Remitente_ultimo } else { '' }
                Num_Mensajes    = if ($row.Num_Mensajes)    { [int]$row.Num_Mensajes }       else { 0 }
                MessageIds      = if ($row.MessageIds)      { [string]$row.MessageIds }      else { '' }
                OutlookUrls     = if ($row.OutlookUrls)     { [string]$row.OutlookUrls }     else { '' }
                Revision        = $revisionTimestamp
                IdActuacion     = 0
                Body            = if ($row.Body)            { [string]$row.Body }            else { '' }
                IsBodyHTML      = if ($row.IsBodyHTML)      { 1 }                            else { 0 }
                To              = if ($row.To)              { [string]$row.To }              else { '' }
                Cc              = if ($row.Cc)              { [string]$row.Cc }              else { '' }
                User            = if ($row.User)            { [string]$row.User }            else { '' }
            }
            $count++
        }

        Write-Log "Exportados $count registros a SQLite: $DatabasePath" "INFO"
    }



    # =================================================================================
    # FILTROS CONFIGURABLES
    # =================================================================================
    # Modo:
    # - Exclude => si cumple, el mensaje se descarta
    # - Include => reservado por si quieres reutilizar el motor
    #
    # L�gica:
    # - AND / OR
    #
    # Condiciones:
    # Field  = From | Domain | Subject | Body | Folder
    # Type   = Contains | NotContains | Equals | NotEquals | Regex | NotRegex
    #
    # NOTA: La l�gica aplicada aqu�� replica tu �ltima definici�n:
    # "Ignora correos que procedan de X y su asunto NO tenga el texto Y"
    # es decir, se excluyen mensajes de esos remitentes cuando NO cumplen el patr�n esperado.
    # =================================================================================

    $Filters = @(
        @{
            Name = "Incluir Intel sin patr�n Filtraciones DD/MM/YYYY"
            Mode = "Include"
            Logic = "AND"
            Grupo = "Smarthc"
            Conditions = @(
                @{ Field = "From";    Type = "Equals";    Value = "intel@smarthc.es" },
                @{ Field = "Subject"; Type = "Regex";  Value = 'Filtraciones\s+\d{2}/\d{2}/\d{4}' }
            )
        },
        @{
            Name = "Incluir Nexus con Policy Alert"
            Mode = "Include"
            Logic = "AND"
            Grupo = "NexusIQServer"
            Conditions = @(
                @{ Field = "From";    Type = "Equals";      Value = "nexusiqserver@tirea.es" },
                @{ Field = "Subject"; Type = "Contains"; Value = "Policy Alert" }
            )
        },
        @{
            Name = "Incluir Imperva sin Attack Report is Ready"
            Mode = "Include"
            Logic = "AND"
            Grupo = "Imperva"
            Conditions = @(
                @{ Field = "From";    Type = "Equals";      Value = "no_reply@out.imperva.com" },
                @{ Field = "Subject"; Type = "Contains"; Value = "Attack Report is Ready" }
            )
        },
        @{
            Name = "Incluir Aiuken con Case #"
            Mode = "Include"
            Logic = "AND"
            Grupo = "Aiuken"
            Conditions = @(
                @{ Field = "From";    Type = "Equals";      Value = "support@aiuken.com" },
                @{ Field = "Subject"; Type = "Contains"; Value = "Case #" }
            )
        },
        @{
            Name = "Incluir Aiuken con Ticket#"
            Mode = "Include"
            Logic = "AND"
            Grupo = "Aiuken"
            Conditions = @(
                @{ Field = "From";    Type = "Equals";      Value = "support@aiuken.com" },
                @{ Field = "Subject"; Type = "Contains"; Value = "Ticket#" }
            )
        },
        @{
            Name = "Incluir operacionescloud con CRQ"
            Mode = "Include"
            Logic = "AND"
            Grupo = "Telefonica"
            Conditions = @(
                @{ Field = "From";    Type = "Equals";      Value = "operacionescloudms.tcct@telefonica.com" },
                @{ Field = "Subject"; Type = "Contains"; Value = "CRQ" }
            )
        },
        @{
            Name = "Tickets de RT"
            Mode = "Include"
            Logic = "AND"
            Grupo = "RT"
            Conditions = @(
                @{ Field = "From";    Type = "Contains";     Value = ".rt@tirea.es" },
                @{ Field = "Subject"; Type = "Regex"; Value = ".+\[\D+\ \#\d+\].+" }
            )
        },
        @{
            Name = "Alarmas CrowdStrike"
            Mode = "Include"
            Logic = "AND"
            Grupo = "CrowdStrike"
            Conditions = @(
                @{ Field = "From";    Type = "Equals";       Value = "falcon@crowdstrike.com" },
                @{ Field = "Subject"; Type = "Contains"; Value = "New detection" }
            )
        },
        @{
            Name = "Alerta SOAR"
            Mode = "Include"
            Logic = "AND"
            Grupo = "Telefonica"
            Conditions = @(
                @{ Field = "From";    Type = "Equals";       Value = "no-reply-soar@cybersecurity.telefonica.com" },
                @{ Field = "Subject"; Type = "Contains"; Value = "INC000" }
            )
        },
        @{
            Name = "Identidad/Autorizacion"
            Mode = "Include"
            Logic = "AND"
            Grupo = "Telefonica"
            Conditions = @(
                @{ Field = "From";    Type = "Equals";       Value = "itsmtelefonicatech@service-now.com" },
                @{ Field = "Subject"; Type = "Contains"; Value = "Case CS00" }
            )
        },
        @{
            Name = "Soporte Telefonica"
            Mode = "Include"
            Logic = "AND"
            Grupo = "Telefonica"
            Conditions = @(
                @{ Field = "From";    Type = "Contains";       Value = "@telefonica.com" },
                @{ Field = "Subject"; Type = "Contains"; Value = "INC00" }
            )
        },
        @{
            Name = "Soporte Telefonica"
            Mode = "Include"
            Logic = "AND"
            Grupo = "Telefonica"
            Conditions = @(
                @{ Field = "From";    Type = "Contains";       Value = "argonauta.no-reply@sdesk.telefonica.es" },
                @{ Field = "Subject"; Type = "Contains"; Value = "INC00" }
            )
        },
        @{
            Name = "Soporte Telefonica2"
            Mode = "Include"
            Logic = "AND"
            Grupo = "Telefonica"
            Conditions = @(
                @{ Field = "From";    Type = "Contains";       Value = "servicedesk.tcct@telefonica.com" },
                @{ Field = "Subject"; Type = "Contains"; Value = "CS00" }
            )
        },
        @{
            Name = "Tirea"
            Mode = "Include"
            Logic = "AND"
            Grupo = "Telefonica"
            Conditions = @(
                @{ Field = "From";    Type = "Contains";       Value = "@tirea.es" },
                @{
                    Logic = "OR"
                    Conditions = @(
                        @{ Field = "Subject"; Type = "Contains"; Value = "CS00" },
                        @{ Field = "Subject"; Type = "Contains"; Value = "INC00" },
                        @{ Field = "Subject"; Type = "Contains"; Value = "CRQ00" }
                    )
                }
            )
        }

        # Ejemplo de filtro adicional fácil de personalizar:
        # @{
        #     Name = "Excluir newsletter"
        #     Mode = "Exclude"
        #     Logic = "OR"
        #     Conditions = @(
        #         @{ Field = "Subject"; Type = "Contains"; Value = "newsletter" },
        #         @{ Field = "Body";    Type = "Contains"; Value = "unsubscribe" }
        #     )
        # }
    )



    ###
    ### Programa principal
    ###

    <#
    $Outlook = New-Object -ComObject Outlook.Application
    $Namespace = $Outlook.GetNamespace("MAPI")

    ## # Carpeta bandeja de entrada (ajustar si es necesario)
    $Inbox = $Namespace.GetDefaultFolder(6)
    # Subcarpeta "_Check_MK"
    # $subfolder = $Inbox.Folders.Item("_Check_MK")
    $subfolder = $Inbox  #solo los ficheros de la bandeja de entrada excluidas sus susbcarpetas

    ##$MailFolderName = "Bandeja de entrada"
    ## $folderId = Resolve-MailFolderId -UserId $UserId -FolderName $MailFolderName



    ### Carpeta destino
    ##$dest = "C:\Temp\DMARC"
    ##if (!(Test-Path $dest)) {
    ##    New-Item -ItemType Directory -Path $dest | Out-Null
    ##}

    # Fecha actual
    $FechaFin = Get-Date

    <!-- # Items ordenados por fecha descendente
    # $items = $Inbox.Items | Sort-Object -Property ReceivedTime -Descending

    $fechaInicio = $FechaInicio.ToString("g")

    $filtro = "[ReceivedTime] >= '$fechaInicio'"

    Write-Host "Filtro: $filtro"

    # $items = $Inbox.Items.Restrict($filtro) |
    #     Sort-Object ReceivedTime -Descending
    $items = $Inbox.Items |
        Where-Object {
                $_.ReceivedTime -ge $fechaInicio -and
                $_.ReceivedTime -le $fechaFin
            }  |
        Sort-Object -Property ReceivedTime -Descending
     !-->
     

    if( -not $fechaInicio ) {
        # Calcular fecha de hace 1 mes
        $fechaInicio = (Get-Date).AddMonths(-1)
    }

    $fechaFin = Get-Date

    Write-Host "Filtrando correos desde $fechaInicio hasta $fechaFin en: $($subfolder.name)"


    # Construir filtro (formato requerido por Outlook)
    $filtro = "[ReceivedTime] >= '" + $fechaInicio.ToString("g") + "' AND [ReceivedTime] <= '" + $fechaFin.ToString("g") + "'"

    # Filtrar con Restrict (MUCHO más eficiente)
    # $items = $inbox.Items.Restrict($filtro)
    $items = $subfolder.Items.Restrict($filtro)

    # Ordenar resultados
    $items = $items | Sort-Object ReceivedTime -Descending

    # Mostrar resultados
    # $items | Select-Object Subject, SenderName, ReceivedTime | Format-Table -AutoSize







    Write-Host "Correos recuperados por fecha: $($items.count)"

    $seguir= ""
    $FilteredMails = @()

    foreach ($mail in $items) {
        $mail2 = Normalize-Message -Message $mail -FolderDisplayName $subfolder.name 
        $received = $mail2.ReceivedTime
        $ignorar = $true
        if ( -not ( Apply-Filters -Mail $mail2 -Filters $Filters ) ) {
            $FilteredMails += $mail2
            $ignorar = $false
        }
        $subject = $mail2.Subject.ToLower()
        if( $ignorar ) {
            Write-Host "Ign -> Fecha: $received -> ${$Mail2.From} $subject"
        } else {
            Write-Host "OK  -> Fecha: $received -> ${$Mail2.From} $subject"
        }
        if( -not $seguir ) {
            $seguir = Read-Host "Seguir (a -> continuar sin preguntar)" 
            if( $seguir -ne "a" ){
                $seguir = ""
            }
        }
    }

    #>


    # $UserId = "Fernando.Lopez@tirea.es"
    # $MailFolderName = "Bandeja de entrada"
    # $DaysBack = 3


    # $TemplatePath = "C:\ps1\tickets_telefonica.xlsx"
    # $WorksheetName = "Tickets"
    # $OutputPath = "C:\ps1\"

    # $InstallDependencies = $true

    # $Scope= "CurrentUser"

    # Para que muestre mensajes de depuración
    # $VerboseLogging = $false

    # Obtener usuario conectado
    Connect-GraphIfNeeded

    if( -not $UserId ) { 
        Write-Log "Obteniendo UserId" "INFO"
        $ctx = Get-MgContext -ErrorAction SilentlyContinue
        $user = Get-MgUser -UserId $ctx.Account -ErrorAction SilentlyContinue
        if ( $user ) {
            Write-Log "Usuario conectado: $($user.UserPrincipalName)" "INFO"
        } else {
            Write-Log "No se pudo obtener el usuario conectado. Aseg�rate de haber iniciado sesion con Connect-MgGraph." "ERROR"
            throw "No se pudo obtener el usuario conectado. Aseg�rate de haber iniciado sesion con Connect-MgGraph."
        }
        $UserId = $user.Id
        # Write-Log "Obtenido User: ($user.UserPrincipalName)" "INFO"
    }

    # Dependencias
    Ensure-Module -Name "Microsoft.Graph.Authentication" -TryInstall:$InstallDependencies -InstallScope $Scope
    Ensure-Module -Name "Microsoft.Graph.Mail"           -TryInstall:$InstallDependencies -InstallScope $Scope
    Ensure-Module -Name "ImportExcel"                    -TryInstall:$InstallDependencies -InstallScope $Scope
    Ensure-Module -Name "PSSQLite"                       -TryInstall:$InstallDependencies -InstallScope $Scope

    if( $MailFolderName -eq "Bandeja de entrada" ) {
        $folderId = Resolve-MailFolderId -UserId $UserId -FolderName $MailFolderName
    } else {
        $folderIdInput = Resolve-MailFolderId -UserId $UserId -FolderName "Bandeja de entrada"
        $fId = Find-MailFolderRecursive -UserId $UserId -ParentFolderId $folderIdInput -FolderName $MailFolderName
        Write-Log "Encontrada subcarpeta -> $($fId.DisplayName)" "INFO"
        $folderId= $fId.Id
    }

    $folderIdMove = $null
    if ( $MailFolderNameMove ) {
        $folderIdMove = Find-MailFolderRecursive -UserId $UserId -ParentFolderId $folderId -FolderName $MailFolderNameMove
        # $folderIdMove = ( Get-MgUserMailFolderChildFolder `
        #         -UserId $UserId `
        #         -MailFolderId $folderId ).Where({ $_.DisplayName -eq $MailFolderNameMove }).Id
        # # $folderIdMove = Resolve-MailFolderId -UserId $UserId -FolderName $MailFolderNameMove
        if($folderIdMove) {
            Write-Log "Subcarpeta destino encontrada: $MailFolderNameMove -> $folderIdMove" "DEBUG"
        } else {
            Write-Log "No se encontr� la subcarpeta destino: $MailFolderNameMove. Se mantendr�n los correos en su ubicaci�n original." "WARN"
        }
    } else {
        Write-Log "No se mueven los mensajes" "INFO"
    }

    $since = (Get-Date).AddDays(-$DaysBack)

    # Write-Host "Filtrando correos desde $since hasta ahora en: $MailFolderName"
    Write-Log "Filtrando correos desde $since hasta ahora en: $MailFolderName" "INFO"


    $revisionTimestamp = Get-Date -Format "yyyyMMdd-HHmmss"

    $rawMessages = Get-MailMessagesFromFolder -UserId $UserId -MailFolderId $folderId -ReceivedAfter $since

    # Write-Host "Correos iniciales: $($rawMessages.Count)"
    Write-Log "Correos iniciales: $($rawMessages.Count)" "INFO"

    $seguir= "a"
    $FilteredMails = @()

    foreach ($mail in $rawMessages) {
        $mail2 = Normalize-Message -Message $mail -FolderDisplayName $MailFolderName -Revision $revisionTimestamp
        # $received = $mail2.ReceivedTime
        $received = $mail2.receivedDateTime
        $Filtro = ""
        $Grupo = ""
        $ignorar = Apply-Filters -Mail $mail2 -Filters $Filters -Fil1 ([ref]$Filtro) -Grupo1 ([ref]$Grupo)
        if ( -not ( $ignorar ) ) {
            $mail2.Grupo = $Grupo
            $mail2.Filtro = $Filtro
            $FilteredMails += $mail2
        }
        $subject = $mail2.Subject.ToLower()
        if( $ignorar ) {
            # Write-Host "Ign -> Fecha: $received -> ${$Mail2.From} $subject"
            Write-Log "Ign -> Fecha: $received -> ${$Mail2.From} $subject" "DEBUG"
        } else {
            # Write-Host "OK  -> Fecha: $received -> ${$Mail2.From} $subject"
            Write-Log "OK  -> Fecha: $received -> $($Mail2.From) $subject -> $($mail.Id) " "DEBUG"
        }
        if( -not $seguir ) {
            $seguir = Read-Host "Seguir (a -> continuar sin preguntar)" 
            if( $seguir -ne "a" ){
                $seguir = ""
            }
        }
    }

    # Write-Host ""
    # Write-Host "Correos encontrados: $($FilteredMails.Count)/$($rawMessages.Count)"
    Write-Log "" "INFO"
    Write-Log "Correos encontrados: $($FilteredMails.Count)/$($rawMessages.Count)" "INFO"

	if( $folderIdMove -and $FilteredMails.Count -gt 0 ) {
		Write-Log "Moviendo correos a la carpeta: $MailFolderNameMove" "INFO"
		foreach( $fmail in $FilteredMails ) {
			try {
				# $message = Get-MgUserMessage -UserId "me" -MessageId $fmail.Id
				# $message = Get-MgUserMessage -UserId $UserId -MessageId $fmail.Id
				# $received = $fmail.receivedDateTime
				# $subject = $fmail.Subject
				Write-Log "Antes ID: $($fmail.MessageId) Moviendo correo: $($fmail.receivedDateTime) $($fmail.Subject)" "DEBUG"
				# Write-Log "Moviendo correo: $($message.Id)" "INFO"
				# Move-MgUserMessage -UserId $UserId -MessageId $message.Id -DestinationId $folderIdMove.Id
				# Marca como leido
				Update-MgUserMessage -UserId $UserId -MessageId $fmail.Id -BodyParameter @{ isRead = $true }
				# Mueve a la carpeta elegida
				Move-MgUserMessage -UserId $UserId -MessageId $fmail.Id -DestinationId $folderIdMove.Id
				$fmail.MessageId = $fmail.MessageId
				Write-Log "Antes ID: $($fmail.MessageId) Moviendo correo: $($fmail.receivedDateTime) $($fmail.Subject)" "DEBUG"
				# Move-MgUserMailFolderMessage -UserId $UserId -MessageId $mail.MessageId -MailFolderId $mail.ParentFolderId -DestinationId $folderIdMove        
				# Move-MgUserMailFolderMessage -UserId $UserId -MailFolderId $mail.ParentFolderId -MessageId $mail.MessageId -DestinationId $folderIdMove        
				# se marcan como leidos
			} catch {
				Write-Log "Error al mover el correo: $($_.Exception.Message)" "ERROR"
				# Write-Log "Error al mover el correo: $($mail.MessageId) -> $($_.Exception.Message)" "ERROR"
			}
		}
	}

    if( $FilteredMails.Count -gt 0 ) {
        $Rows= Build-OutputRows -Messages $FilteredMails -UserPrincipalName $user.UserPrincipalName

        # Write-Host "Grupos encontrados: $($Rows.Count)/$($FilteredMails.Count)/$($rawMessages.Count)"
        Write-Log "Grupos encontrados: $($Rows.Count)/$($FilteredMails.Count)/$($rawMessages.Count)" "INFO"

        $salida = $OutputPath + (Get-Date -Format "yyyyMMdd_HHmmss") + ".xlsx"

        Export-ResultExcel -Rows $Rows -TemplatePath $TemplatePath -OutputPath $salida -Overwrite $true -WorksheetName $WorksheetName

        if ($outBBDD) {
            Export-ResultSqlite -Rows $Rows -DatabasePath $outBBDD
        }

    } else{
        Write-Log "No se encontraron correos que cumplan los criterios de filtrado. No se generar� el Excel ni se mover�n correos." "WARN"
        return
    }

}
