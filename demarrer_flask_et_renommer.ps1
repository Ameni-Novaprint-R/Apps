# Script pour démarrer Flask et exécuter le renommage
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

# Exécuter le renommage via la route Flask
Write-Host ""
Write-Host "Exécution du renommage via Flask..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/admin/renommer-web-droits-acces-en-web-actions" -Method POST -ContentType "application/json" -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop
    $result = $response.Content | ConvertFrom-Json
    Write-Host ""
    Write-Host "Résultat:" -ForegroundColor Cyan
    $result.results | ForEach-Object { Write-Host $_ }
    Write-Host ""
    if ($result.success) {
        Write-Host "Renommage terminé avec succès!" -ForegroundColor Green
        Write-Host "Nombre de lignes: $($result.row_count)" -ForegroundColor Green
    } else {
        Write-Host "Erreur: $($result.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "Erreur lors de l'appel de la route: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
