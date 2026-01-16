# Script PowerShell pour supprimer les fichiers __pycache__ du projet 19
# A executer depuis le repertoire racine du projet (C:\Apps)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NETTOYAGE DU CACHE PYTHON - PROJET 19" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Aller dans le repertoire du script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "Repertoire de travail: $PWD" -ForegroundColor Green
Write-Host ""

# Supprimer __pycache__ dans routes/
Write-Host "Suppression de routes\__pycache__..." -ForegroundColor Yellow
if (Test-Path "routes\__pycache__") {
    Remove-Item -Path "routes\__pycache__" -Recurse -Force
    Write-Host "[OK] routes\__pycache__ supprime" -ForegroundColor Green
} else {
    Write-Host "[INFO] routes\__pycache__ n'existe pas" -ForegroundColor Gray
}
Write-Host ""

# Supprimer __pycache__ a la racine
Write-Host "Suppression de __pycache__ a la racine..." -ForegroundColor Yellow
if (Test-Path "__pycache__") {
    Remove-Item -Path "__pycache__" -Recurse -Force
    Write-Host "[OK] __pycache__ supprime" -ForegroundColor Green
} else {
    Write-Host "[INFO] __pycache__ n'existe pas" -ForegroundColor Gray
}
Write-Host ""

# Supprimer les fichiers .pyc individuels dans routes/
Write-Host "Suppression des fichiers .pyc dans routes\..." -ForegroundColor Yellow
$pycFiles = Get-ChildItem -Path "routes\" -Filter "*.pyc" -ErrorAction SilentlyContinue
if ($pycFiles) {
    $pycFiles | Remove-Item -Force
    Write-Host "[OK] Fichiers .pyc supprimes dans routes\" -ForegroundColor Green
} else {
    Write-Host "[INFO] Aucun fichier .pyc trouve dans routes\" -ForegroundColor Gray
}
Write-Host ""

# Supprimer les fichiers .pyc individuels a la racine
Write-Host "Suppression des fichiers .pyc a la racine..." -ForegroundColor Yellow
$pycFilesRoot = Get-ChildItem -Path "." -Filter "*.pyc" -ErrorAction SilentlyContinue
if ($pycFilesRoot) {
    $pycFilesRoot | Remove-Item -Force
    Write-Host "[OK] Fichiers .pyc supprimes a la racine" -ForegroundColor Green
} else {
    Write-Host "[INFO] Aucun fichier .pyc trouve a la racine" -ForegroundColor Gray
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NETTOYAGE TERMINE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Vous pouvez maintenant redemarrer le serveur Flask" -ForegroundColor Yellow
Write-Host "avec: python app.py" -ForegroundColor Yellow
Write-Host ""
