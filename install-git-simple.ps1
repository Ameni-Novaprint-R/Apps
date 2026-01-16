# Script d'installation simple de Git pour Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INSTALLATION DE GIT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si Git est déjà installé
try {
    $gitVersion = git --version 2>$null
    if ($gitVersion) {
        Write-Host "Git est deja installe: $gitVersion" -ForegroundColor Green
        exit 0
    }
} catch {
    # Git n'est pas installe
}

# Essayer winget
Write-Host "Tentative d'installation via winget..." -ForegroundColor Cyan
$winget = Get-Command winget -ErrorAction SilentlyContinue
if ($winget) {
    Write-Host "Installation de Git via winget..." -ForegroundColor Green
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    Write-Host "Installation terminee! Redemarrez PowerShell." -ForegroundColor Green
    exit 0
}

# Essayer Chocolatey
Write-Host "Tentative d'installation via Chocolatey..." -ForegroundColor Cyan
$choco = Get-Command choco -ErrorAction SilentlyContinue
if ($choco) {
    Write-Host "Installation de Git via Chocolatey..." -ForegroundColor Green
    choco install git -y
    Write-Host "Installation terminee! Redemarrez PowerShell." -ForegroundColor Green
    exit 0
}

# Téléchargement et installation automatique
Write-Host "Telechargement et installation automatique de Git..." -ForegroundColor Cyan
Write-Host ""

$gitInstallerUrl = "https://github.com/git-for-windows/git/releases/latest/download/Git-2.43.0-64-bit.exe"
$installerPath = "$env:TEMP\Git-Installer.exe"

try {
    Write-Host "Telechargement en cours..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $gitInstallerUrl -OutFile $installerPath -UseBasicParsing
    
    Write-Host "Installation en cours (cela peut prendre quelques minutes)..." -ForegroundColor Cyan
    Start-Process -FilePath $installerPath -ArgumentList "/VERYSILENT", "/NORESTART" -Wait
    
    Write-Host ""
    Write-Host "Installation terminee!" -ForegroundColor Green
    Write-Host "IMPORTANT: Redemarrez PowerShell pour que Git soit disponible." -ForegroundColor Yellow
    
    Remove-Item $installerPath -ErrorAction SilentlyContinue
} catch {
    Write-Host "Erreur: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Ouverture de la page de telechargement..." -ForegroundColor Yellow
    Start-Process "https://git-scm.com/download/win"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
