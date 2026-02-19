param()

$logFile = ".\index_creation.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Log {
    param($Message)
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $logFile -Value $logMessage
}

Write-Log "======================================================================"
Write-Log "INICIANDO CREACION DE INDICE DE AZURE AI SEARCH"
Write-Log "======================================================================"

$searchEndpoint = "https://search-analyzer-prod.search.windows.net"
$searchKey = $env:AZURE_SEARCH_ADMIN_KEY  # Configurar variable de entorno antes de ejecutar
$indexName = "torres-index"
$apiVersion = "2024-07-01"

$headers = @{
    "Content-Type" = "application/json"
    "api-key" = $searchKey
}

# PASO 1: Eliminar índice existente
Write-Log ""
Write-Log "PASO 1: Eliminando indice existente..."
try {
    $deleteUrl = "$searchEndpoint/indexes/$indexName`?api-version=$apiVersion"
    $response = Invoke-RestMethod -Uri $deleteUrl -Method Delete -Headers @{"api-key"=$searchKey} -ErrorAction SilentlyContinue
    Write-Log "OK - Indice eliminado"
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Log "OK - Indice no existia"
    } else {
        Write-Log "WARNING - Error eliminando: $($_.Exception.Message)"
    }
}
Start-Sleep -Seconds 2

# PASO 2: Crear índice
Write-Log ""
Write-Log "PASO 2: Creando indice..."
$indexSchema = @{
    name = $indexName
    fields = @(
        @{name="id"; type="Edm.String"; key=$true; searchable=$false}
        @{name="team_name"; type="Edm.String"; searchable=$true; filterable=$true; sortable=$true}
        @{name="tower"; type="Edm.String"; searchable=$true; filterable=$true; sortable=$true}
        @{name="team_lead"; type="Edm.String"; searchable=$true}
        @{name="team_lead_email"; type="Edm.String"; searchable=$false; filterable=$true}
        @{name="skills"; type="Collection(Edm.String)"; searchable=$true; filterable=$true}
        @{name="technologies"; type="Collection(Edm.String)"; searchable=$true; filterable=$true}
        @{name="expertise_areas"; type="Collection(Edm.String)"; searchable=$true; filterable=$true}
        @{name="frameworks"; type="Collection(Edm.String)"; searchable=$true; filterable=$true}
        @{name="description"; type="Edm.String"; searchable=$true}
    )
}

try {
    $createUrl = "$searchEndpoint/indexes?api-version=$apiVersion"
    $body = $indexSchema | ConvertTo-Json -Depth 10
    $response = Invoke-RestMethod -Uri $createUrl -Method Post -Headers $headers -Body $body
    Write-Log "OK - Indice creado exitosamente"
} catch {
    Write-Log "ERROR - No se pudo crear indice: $($_.Exception.Message)"
    Write-Log $_.Exception.Response
    exit 1
}
Start-Sleep -Seconds 2

# PASO 3: Cargar documentos
Write-Log ""
Write-Log "PASO 3: Cargando documentos de torres..."
try {
    $torresData = Get-Content -Path ".\data\torres_data_prod.json" -Raw | ConvertFrom-Json
    Write-Log "Documentos a cargar: $($torresData.Count)"
    
    $documents = @()
    foreach ($torre in $torresData) {
        $doc = @{
            "@search.action" = "upload"
            id = $torre.id
            team_name = $torre.team_name
            tower = $torre.tower
            team_lead = $torre.team_lead
            team_lead_email = $torre.team_lead_email
            skills = $torre.skills
            technologies = $torre.technologies
            expertise_areas = $torre.expertise_areas
            frameworks = if($torre.frameworks) { $torre.frameworks } else { @() }
            description = $torre.description
        }
        $documents += $doc
    }
    
    $uploadPayload = @{ value = $documents }
    $uploadUrl = "$searchEndpoint/indexes/$indexName/docs/index?api-version=$apiVersion"
    $uploadBody = $uploadPayload | ConvertTo-Json -Depth 10
    
    $response = Invoke-RestMethod -Uri $uploadUrl -Method Post -Headers $headers -Body $uploadBody
    Write-Log "OK - Documentos cargados exitosamente"
    
} catch {
    Write-Log "ERROR - No se pudieron cargar documentos: $($_.Exception.Message)"
    Write-Log $_.Exception.Response
    exit 1
}
Start-Sleep -Seconds 3

# PASO 4: Verificar
Write-Log ""
Write-Log "PASO 4: Verificando indice creado..."
try {
    $countUrl = "$searchEndpoint/indexes/$indexName/docs/`$count?api-version=$apiVersion"
    $count = Invoke-RestMethod -Uri $countUrl -Method Get -Headers @{"api-key"=$searchKey}
    Write-Log "Documentos en el indice: $count"
    
    if ($count -eq 13) {
        Write-Log ""
        Write-Log "======================================================================"
        Write-Log "EXITO! Indice creado correctamente con 13 torres"
        Write-Log "======================================================================"
    } else {
        Write-Log "WARNING - Se esperaban 13 documentos, se encontraron $count"
    }
} catch {
    Write-Log "ERROR - No se pudo verificar: $($_.Exception.Message)"
}

Write-Log ""
Write-Log "PROCESO COMPLETADO - Ver detalles en: $logFile"
