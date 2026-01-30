# Script PowerShell pour redémarrer Flask simplement
# Ce script arrête Flask et le redémarre pour charger les nouvelles modifications

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "REDEMARRAGE DE FLASK" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Étape 1: Arrêter Flask
Write-Host "[1/3] Arrêt des processus Flask existants..." -ForegroundColor Yellow

# Trouver et arrêter les processus Python qui utilisent le port 5000
$processes = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($processes) {
    foreach ($pid in $processes) {
        Write-Host "  Arrêt du processus PID $pid..." -ForegroundColor Gray
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "  Aucun processus Flask trouvé sur le port 5000" -ForegroundColor Gray
}

Start-Sleep -Seconds 2

# Étape 2: Vérifier que le port est libre
Write-Host ""
Write-Host "[2/3] Vérification du port 5000..." -ForegroundColor Yellow

$portInUse = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "  [ATTENTION] Le port 5000 est encore utilisé." -ForegroundColor Red
    Write-Host "  Fermez manuellement les processus Flask avant de continuer." -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour continuer quand même"
} else {
    Write-Host "  [OK] Le port 5000 est libre." -ForegroundColor Green
}

# Étape 3: Démarrer Flask
Write-Host ""
Write-Host "[3/3] Démarrage de Flask..." -ForegroundColor Yellow
Write-Host ""

$venvPath = Join-Path $scriptPath "venv"
$appPath = Join-Path $scriptPath "app.py"

if (Test-Path $venvPath) {
    Write-Host "  Utilisation de l'environnement virtuel..." -ForegroundColor Gray
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; & '$activateScript'; python '$appPath'"
} else {
    Write-Host "  Pas d'environnement virtuel trouvé, utilisation de Python système..." -ForegroundColor Gray
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; python '$appPath'"
}

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Flask a été redémarré dans une nouvelle fenêtre." -ForegroundColor Green
Write-Host "Les modifications devraient maintenant être chargées." -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
