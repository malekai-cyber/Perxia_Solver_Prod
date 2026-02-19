# Script para crear índice de Azure AI Search y poblar con torres
# PRODUCCIÓN

$SEARCH_ENDPOINT = "https://search-analyzer-prod.search.windows.net"
$SEARCH_KEY = $env:AZURE_SEARCH_ADMIN_KEY  # Configurar variable de entorno antes de ejecutar
$INDEX_NAME = "torres-index"
$API_VERSION = "2024-07-01"

Write-Host "=== CREANDO ÍNDICE AZURE AI SEARCH ===" -ForegroundColor Cyan
Write-Host "Endpoint: $SEARCH_ENDPOINT"
Write-Host "Índice: $INDEX_NAME`n"

# 1. Crear índice
Write-Host "1. Creando índice..." -ForegroundColor Yellow
$schema = @{
    name = $INDEX_NAME
    fields = @(
        @{name="id"; type="Edm.String"; key=$true}
        @{name="team_name"; type="Edm.String"; searchable=$true}
        @{name="tower"; type="Edm.String"; searchable=$true; filterable=$true}
        @{name="description"; type="Edm.String"; searchable=$true}
        @{name="team_lead"; type="Edm.String"; searchable=$true}
        @{name="team_lead_email"; type="Edm.String"}
        @{name="skills"; type="Collection(Edm.String)"; searchable=$true}
        @{name="technologies"; type="Collection(Edm.String)"; searchable=$true}
        @{name="expertise_areas"; type="Collection(Edm.String)"; searchable=$true}
    )
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod `
        -Uri "$SEARCH_ENDPOINT/indexes/${INDEX_NAME}?api-version=$API_VERSION" `
        -Method PUT `
        -Body $schema `
        -ContentType "application/json" `
        -Headers @{"api-key"=$SEARCH_KEY}
    Write-Host "   ✅ Índice creado exitosamente" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 'Conflict') {
        Write-Host "   ⚠️  Índice ya existe, continuando..." -ForegroundColor Yellow
    } else {
        Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 2. Cargar torres
Write-Host "`n2. Cargando datos de torres..." -ForegroundColor Yellow
$torresData = Get-Content "data/torres_nuevas.json" -Raw | ConvertFrom-Json

$documents = @()
foreach ($torre in $torresData) {
    $doc = @{
        "@search.action" = "mergeOrUpload"
        id = $torre.tower.ToLower() -replace " ", "-"
        team_name = $torre.tower
        tower = $torre.tower
        description = if ($torre.description) { $torre.description } else { "" }
        team_lead = $torre.team_lead
        team_lead_email = $torre.team_lead_email
        skills = $torre.skills
        technologies = $torre.technologies
        expertise_areas = $torre.expertise_areas
    }
    $documents += $doc
}

Write-Host "   📋 $($documents.Count) torres preparadas"

# 3. Upload batch
Write-Host "`n3. Subiendo documentos al índice..." -ForegroundColor Yellow
$payload = @{value = $documents} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod `
        -Uri "$SEARCH_ENDPOINT/indexes/${INDEX_NAME}/docs/index?api-version=$API_VERSION" `
        -Method POST `
        -Body $payload `
        -ContentType "application/json" `
        -Headers @{"api-key"=$SEARCH_KEY}
    
    $successCount = ($response.value | Where-Object { $_.status }).Count
    Write-Host "   ✅ $successCount torres subidas exitosamente" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Verificar
Write-Host "`n4. Verificando índice..." -ForegroundColor Yellow
try {
    $count = Invoke-RestMethod `
        -Uri "$SEARCH_ENDPOINT/indexes/${INDEX_NAME}/docs/`$count?api-version=$API_VERSION" `
        -Method GET `
        -Headers @{"api-key"=$SEARCH_KEY}
    Write-Host "   📊 Total de documentos en índice: $count" -ForegroundColor Cyan
} catch {
    Write-Host "   ⚠️  No se pudo verificar el conteo" -ForegroundColor Yellow
}

Write-Host "`n=== ✅ COMPLETADO ===" -ForegroundColor Green
