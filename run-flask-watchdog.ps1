# Script PowerShell pour lancer Flask avec Watchdog
# Rechargement automatique lors des modifications de fichiers

Set-Location "C:\Apps"

# Activer l'environnement virtuel
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
} else {
    Write-Error "Environnement virtuel non trouvé dans .\venv\Scripts\Activate.ps1"
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FLASK AVEC WATCHDOG" -ForegroundColor Cyan
Write-Host "Rechargement automatique activé" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier que watchdog est installé
try {
    python -c "import watchdog" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Watchdog n'est pas installé. Installation en cours..."
        pip install watchdog
    }
} catch {
    Write-Warning "Erreur lors de la vérification de watchdog"
}

# Lancer Flask avec watchdog
Write-Host "Démarrage de Flask avec Watchdog..." -ForegroundColor Yellow
Write-Host "Appuyez sur Ctrl+C pour arrêter" -ForegroundColor Yellow
Write-Host ""

try {
    python run_flask_with_watchdog.py
} catch {
    Write-Error "Erreur lors du lancement: $_"
    exit 1
} finally {
    Write-Host ""
    Write-Host "Flask arrêté." -ForegroundColor Yellow
}
