# Script simple pour que Cursor démarre Flask automatiquement
# Ce script vérifie si Flask tourne et le démarre si nécessaire

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Vérifier si Flask répond
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[INFO] Flask est déjà en cours d'exécution" -ForegroundColor Green
    exit 0
} catch {
    # Flask n'est pas en cours, le démarrer
    Write-Host "[INFO] Démarrage de Flask..." -ForegroundColor Yellow
    
    $venvPath = Join-Path $scriptPath "venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "[ERREUR] Environnement virtuel introuvable" -ForegroundColor Red
        exit 1
    }
    
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    $flaskScript = Join-Path $scriptPath "run_flask_with_watchdog.py"
    if (-not (Test-Path $flaskScript)) {
        $flaskScript = Join-Path $scriptPath "app.py"
    }
    
    # Démarrer Flask en arrière-plan
    Start-Process powershell -ArgumentList "-WindowStyle Minimized", "-Command", "cd '$scriptPath'; & '$activateScript'; python '$flaskScript'"
    
    # Attendre le démarrage
    $maxWait = 10
    for ($i = 1; $i -le $maxWait; $i++) {
        Start-Sleep -Seconds 1
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            Write-Host "[SUCCES] Flask démarré avec succès!" -ForegroundColor Green
            exit 0
        } catch {
            # Continue d'attendre
        }
    }
    
    Write-Host "[ATTENTION] Flask ne répond pas encore après $maxWait secondes" -ForegroundColor Yellow
    exit 1
}
