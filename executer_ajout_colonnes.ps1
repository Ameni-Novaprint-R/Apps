# Script pour démarrer Flask et ajouter les colonnes
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "Démarrage de Flask..." -ForegroundColor Yellow

# Démarrer Flask dans une nouvelle fenêtre
if (Test-Path "venv\Scripts\activate.ps1") {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; .\venv\Scripts\Activate.ps1; python app.py"
} else {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; python app.py"
}

# Attendre que Flask soit prêt
Write-Host "Attente du démarrage de Flask..." -ForegroundColor Yellow
$maxWait = 30
for ($i = 1; $i -le $maxWait; $i++) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "Flask est prêt!" -ForegroundColor Green
        break
    } catch {
        if ($i -eq $maxWait) {
            Write-Host "Flask n'a pas démarré après $maxWait secondes" -ForegroundColor Red
            exit 1
        }
    }
}

# Exécuter l'ajout des colonnes via la route Flask
Write-Host ""
Write-Host "Ajout des colonnes CodeProj et Nom_SECTIONS..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/admin/ajouter-colonnes-codeproj-nom-sections" -Method POST -ContentType "application/json" -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop
    $result = $response.Content | ConvertFrom-Json
    Write-Host ""
    Write-Host "Résultat:" -ForegroundColor Cyan
    $result.results | ForEach-Object { Write-Host $_ }
    Write-Host ""
    if ($result.success) {
        Write-Host "Colonnes ajoutées avec succès!" -ForegroundColor Green
        Write-Host "Nombre de lignes mises à jour: $($result.row_count)" -ForegroundColor Green
    } else {
        Write-Host "Erreur: $($result.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "Erreur lors de l'appel de la route: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
