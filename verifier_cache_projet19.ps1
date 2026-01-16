# Script PowerShell pour verifier que les fichiers __pycache__ 
# du projet 19 ont bien ete supprimes

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VERIFICATION DU CACHE PYTHON - PROJET 19" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Aller dans le repertoire du script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "Repertoire de travail: $PWD" -ForegroundColor Green
Write-Host ""

$erreurTrouvee = $false

# Verifier routes\__pycache__
Write-Host "[1] Verification de routes\__pycache__..." -ForegroundColor Yellow
if (Test-Path "routes\__pycache__") {
    Write-Host "[ATTENTION] routes\__pycache__ existe encore!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Contenu de routes\__pycache__:" -ForegroundColor Gray
    Get-ChildItem "routes\__pycache__" | Select-Object Name
    Write-Host ""
    
    $projet19Files = Get-ChildItem "routes\__pycache__" -Filter "*projet19*" -ErrorAction SilentlyContinue
    if ($projet19Files) {
        Write-Host "[ERREUR] Des fichiers projet19 existent encore dans routes\__pycache__!" -ForegroundColor Red
        $erreurTrouvee = $true
        $projet19Files | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Red }
    } else {
        Write-Host "[OK] Aucun fichier projet19 trouve dans routes\__pycache__" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] routes\__pycache__ n'existe pas - Cache supprime" -ForegroundColor Green
}
Write-Host ""

# Verifier __pycache__ a la racine
Write-Host "[2] Verification de __pycache__ a la racine..." -ForegroundColor Yellow
if (Test-Path "__pycache__") {
    Write-Host "[ATTENTION] __pycache__ existe encore!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Contenu de __pycache__:" -ForegroundColor Gray
    Get-ChildItem "__pycache__" | Select-Object Name
    Write-Host ""
    
    $dbFiles = Get-ChildItem "__pycache__" -Filter "db.cpython-*.pyc" -ErrorAction SilentlyContinue
    if ($dbFiles) {
        Write-Host "[ERREUR] db.cpython-*.pyc existe encore!" -ForegroundColor Red
        $erreurTrouvee = $true
        $dbFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Red }
    } else {
        Write-Host "[OK] db.cpython-*.pyc n'existe pas" -ForegroundColor Green
    }
    
    $appFiles = Get-ChildItem "__pycache__" -Filter "app.cpython-*.pyc" -ErrorAction SilentlyContinue
    if ($appFiles) {
        Write-Host "[INFO] app.cpython-*.pyc existe encore (peut etre utilise par d'autres projets)" -ForegroundColor Gray
        $appFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
    } else {
        Write-Host "[OK] app.cpython-*.pyc n'existe pas" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] __pycache__ n'existe pas - Cache supprime" -ForegroundColor Green
}
Write-Host ""

# Recherche globale
Write-Host "[3] Recherche globale de fichiers .pyc contenant 'projet19'..." -ForegroundColor Yellow
$allProjet19Files = Get-ChildItem -Path . -Recurse -Filter "*projet19*.pyc" -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike "*\venv\*" }
if ($allProjet19Files) {
    Write-Host "[ERREUR] Des fichiers projet19.pyc existent encore!" -ForegroundColor Red
    $erreurTrouvee = $true
    $allProjet19Files | ForEach-Object { Write-Host "  - $($_.FullName)" -ForegroundColor Red }
} else {
    Write-Host "[OK] Aucun fichier projet19.pyc trouve" -ForegroundColor Green
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RESUME DE LA VERIFICATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not $erreurTrouvee) {
    Write-Host "[SUCCES] Tous les fichiers __pycache__ du projet 19 ont ete supprimes!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Vous pouvez maintenant redemarrer le serveur Flask" -ForegroundColor Yellow
    Write-Host "avec: python app.py" -ForegroundColor Yellow
} else {
    Write-Host "[ATTENTION] Certains fichiers __pycache__ du projet 19 existent encore!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Relancez le script de nettoyage:" -ForegroundColor Yellow
    Write-Host "nettoyer_cache_projet19_complet.bat" -ForegroundColor Yellow
}

Write-Host ""
