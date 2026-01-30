# Fonction pour vérifier et démarrer Flask automatiquement
# Utilisée par Cursor pour démarrer Flask quand nécessaire

function Start-FlaskIfNeeded {
    param(
        [int]$TimeoutSeconds = 5
    )
    
    $scriptPath = Split-Path -Parent $MyInvocation.PSCommandPath
    Set-Location $scriptPath
    
    # Vérifier si Flask répond
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "[INFO] Flask est déjà en cours d'exécution (Status: $($response.StatusCode))" -ForegroundColor Green
        return $true
    } catch {
        # Flask n'est pas en cours, le démarrer
        Write-Host "[INFO] Flask n'est pas en cours d'exécution. Démarrage..." -ForegroundColor Yellow
        
        # Vérifier l'environnement virtuel
        $venvPath = Join-Path $scriptPath "venv"
        if (-not (Test-Path $venvPath)) {
            Write-Host "[ERREUR] Environnement virtuel 'venv' introuvable" -ForegroundColor Red
            return $false
        }
        
        $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
        if (-not (Test-Path $activateScript)) {
            Write-Host "[ERREUR] Script d'activation introuvable" -ForegroundColor Red
            return $false
        }
        
        # Démarrer Flask en arrière-plan
        $flaskScript = Join-Path $scriptPath "run_flask_with_watchdog.py"
        if (-not (Test-Path $flaskScript)) {
            $flaskScript = Join-Path $scriptPath "app.py"
        }
        
        try {
            # Démarrer Flask dans une nouvelle fenêtre (mais minimisée)
            Start-Process powershell -ArgumentList "-WindowStyle Minimized", "-Command", "cd '$scriptPath'; & '$activateScript'; python '$flaskScript'" -ErrorAction Stop
            
            Write-Host "[INFO] Flask en cours de démarrage..." -ForegroundColor Yellow
            
            # Attendre que Flask démarre
            $maxAttempts = 10
            $attempt = 0
            while ($attempt -lt $maxAttempts) {
                Start-Sleep -Seconds 1
                try {
                    $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
                    Write-Host "[SUCCES] Flask démarré avec succès! (Status: $($response.StatusCode))" -ForegroundColor Green
                    return $true
                } catch {
                    $attempt++
                }
            }
            
            Write-Host "[ATTENTION] Flask ne répond pas après $maxAttempts secondes" -ForegroundColor Yellow
            return $false
            
        } catch {
            Write-Host "[ERREUR] Impossible de démarrer Flask: $_" -ForegroundColor Red
            return $false
        }
    }
}

# La fonction est maintenant disponible après avoir chargé ce script avec: . .\verifier_et_demarrer_flask.ps1
