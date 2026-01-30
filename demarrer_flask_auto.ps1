# Script PowerShell pour démarrer Flask automatiquement
# Ce script peut être exécuté manuellement ou via une tâche planifiée Windows

$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "DEMARRAGE AUTOMATIQUE DE FLASK" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si Flask est déjà en cours d'exécution
$flaskProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*app.py*" -or $_.CommandLine -like "*flask*"
}

if ($flaskProcesses) {
    Write-Host "[INFO] Flask semble déjà être en cours d'exécution." -ForegroundColor Yellow
    Write-Host "       PID(s): $($flaskProcesses.Id -join ', ')" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Voulez-vous arrêter les processus existants et redémarrer Flask? (O/N)"
    if ($response -eq "O" -or $response -eq "o") {
        Write-Host "[INFO] Arrêt des processus Flask existants..." -ForegroundColor Yellow
        $flaskProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    } else {
        Write-Host "[INFO] Démarrage annulé." -ForegroundColor Yellow
        exit 0
    }
}

# Vérifier si l'environnement virtuel existe
$venvPath = Join-Path $scriptPath "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[ERREUR] L'environnement virtuel 'venv' n'existe pas dans $scriptPath" -ForegroundColor Red
    Write-Host "         Créez-le avec: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activer l'environnement virtuel et démarrer Flask
Write-Host "[INFO] Activation de l'environnement virtuel..." -ForegroundColor Green
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-Host "[ERREUR] Script d'activation introuvable: $activateScript" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Démarrage de Flask avec watchdog..." -ForegroundColor Green
Write-Host ""

# Démarrer Flask dans une nouvelle fenêtre PowerShell
$flaskScript = Join-Path $scriptPath "run_flask_with_watchdog.py"
if (Test-Path $flaskScript) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; & '$activateScript'; python run_flask_with_watchdog.py" -WindowStyle Normal
    Write-Host "[SUCCES] Flask a été démarré dans une nouvelle fenêtre PowerShell." -ForegroundColor Green
} else {
    # Fallback: démarrer app.py directement
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath'; & '$activateScript'; python app.py" -WindowStyle Normal
    Write-Host "[SUCCES] Flask a été démarré dans une nouvelle fenêtre PowerShell (mode simple)." -ForegroundColor Green
}

Write-Host ""
Write-Host "[INFO] Attente du démarrage de Flask (5 secondes)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Vérifier que Flask répond
Write-Host "[INFO] Vérification que Flask répond..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[SUCCES] Flask répond correctement! (Status: $($response.StatusCode))" -ForegroundColor Green
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Flask est maintenant accessible sur: http://localhost:5000" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Cyan
} catch {
    Write-Host "[ATTENTION] Flask ne répond pas encore. Attendez quelques secondes supplémentaires." -ForegroundColor Yellow
    Write-Host "            Vérifiez la fenêtre Flask pour d'éventuelles erreurs." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Appuyez sur une touche pour fermer cette fenêtre..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
