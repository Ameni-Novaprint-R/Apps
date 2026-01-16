# Script d'installation automatique de Git pour Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INSTALLATION DE GIT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si Git est déjà installé
$gitPath = $null
$gitPaths = @(
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files (x86)\Git\bin\git.exe",
    "$env:LOCALAPPDATA\Programs\Git\bin\git.exe"
)

try {
    $result = Get-Command git -ErrorAction SilentlyContinue
    if ($result) {
        $gitPath = "git"
    }
} catch {
    # Continuer
}

if (-not $gitPath) {
    foreach ($path in $gitPaths) {
        if (Test-Path $path) {
            $gitPath = $path
            break
        }
    }
}

if ($gitPath) {
    Write-Host "✓ Git est déjà installé: $gitPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "Version installée:" -ForegroundColor Cyan
    & $gitPath --version
    exit 0
}

Write-Host "Git n'est pas installé. Démarrage de l'installation..." -ForegroundColor Yellow
Write-Host ""

# Méthode 1: Essayer avec winget (Windows Package Manager)
Write-Host "Tentative d'installation via winget..." -ForegroundColor Cyan
$winget = Get-Command winget -ErrorAction SilentlyContinue
if ($winget) {
    try {
        Write-Host "winget trouvé. Installation de Git..." -ForegroundColor Green
        winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
        Write-Host ""
        Write-Host "✓ Installation via winget terminée!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Redémarrez PowerShell et vérifiez avec: git --version" -ForegroundColor Yellow
        exit 0
    } catch {
        Write-Host "winget n'est pas disponible ou l'installation a échoué." -ForegroundColor Yellow
    }
} else {
    Write-Host "winget n'est pas disponible." -ForegroundColor Yellow
}

# Méthode 2: Essayer avec Chocolatey
Write-Host ""
Write-Host "Tentative d'installation via Chocolatey..." -ForegroundColor Cyan
$choco = Get-Command choco -ErrorAction SilentlyContinue
if ($choco) {
    try {
        Write-Host "Chocolatey trouvé. Installation de Git..." -ForegroundColor Green
        choco install git -y
        Write-Host ""
        Write-Host "✓ Installation via Chocolatey terminée!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Redémarrez PowerShell et vérifiez avec: git --version" -ForegroundColor Yellow
        exit 0
    } catch {
        Write-Host "L'installation via Chocolatey a échoué." -ForegroundColor Yellow
    }
} else {
    Write-Host "Chocolatey n'est pas disponible." -ForegroundColor Yellow
}

# Méthode 3: Téléchargement manuel
Write-Host ""
Write-Host "Les gestionnaires de paquets ne sont pas disponibles." -ForegroundColor Yellow
Write-Host ""
Write-Host "Options d'installation:" -ForegroundColor Cyan
Write-Host "1. Installation manuelle (recommandé)" -ForegroundColor Green
Write-Host "   - Téléchargez depuis: https://git-scm.com/download/win" -ForegroundColor Cyan
Write-Host "   - Exécutez l'installateur" -ForegroundColor Cyan
Write-Host "   - Utilisez les options par défaut" -ForegroundColor Cyan
Write-Host "   - Redémarrez PowerShell après l'installation" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Installation silencieuse (avancé)" -ForegroundColor Green
Write-Host "   - Je peux télécharger l'installateur et l'exécuter en mode silencieux" -ForegroundColor Cyan
Write-Host ""

$choice = Read-Host "Voulez-vous que je télécharge et installe Git automatiquement? (O/N)"

if ($choice -eq "O" -or $choice -eq "o") {
    Write-Host ""
    Write-Host "Téléchargement de l'installateur Git..." -ForegroundColor Cyan
    
    # URL de téléchargement de Git pour Windows
    $gitInstallerUrl = "https://github.com/git-for-windows/git/releases/latest/download/Git-2.43.0-64-bit.exe"
    $installerPath = "$env:TEMP\Git-Installer.exe"
    
    try {
        # Télécharger l'installateur
        Write-Host "Téléchargement en cours..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri $gitInstallerUrl -OutFile $installerPath -UseBasicParsing
        
        Write-Host "✓ Téléchargement terminé" -ForegroundColor Green
        Write-Host ""
        Write-Host "Installation de Git en mode silencieux..." -ForegroundColor Cyan
        Write-Host "(Cela peut prendre quelques minutes)" -ForegroundColor Yellow
        
        # Installer Git en mode silencieux
        $process = Start-Process -FilePath $installerPath -ArgumentList "/VERYSILENT", "/NORESTART", "/SUPPRESSMSGBOXES" -Wait -PassThru
        
        if ($process.ExitCode -eq 0) {
            Write-Host ""
            Write-Host "✓ Installation terminée!" -ForegroundColor Green
            Write-Host ""
            Write-Host "IMPORTANT: Redémarrez PowerShell pour que Git soit disponible." -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Après redémarrage, vérifiez avec: git --version" -ForegroundColor Cyan
            
            # Nettoyer
            Remove-Item $installerPath -ErrorAction SilentlyContinue
        } else {
            Write-Host ""
            Write-Host "⚠ L'installation automatique a rencontré un problème." -ForegroundColor Yellow
            Write-Host "L'installateur a été téléchargé à: $installerPath" -ForegroundColor Cyan
            Write-Host "Vous pouvez l'exécuter manuellement." -ForegroundColor Yellow
        }
    } catch {
        Write-Host ""
        Write-Host "ERREUR lors du téléchargement ou de l'installation." -ForegroundColor Red
        Write-Host "Erreur: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "Veuillez télécharger et installer Git manuellement depuis:" -ForegroundColor Yellow
        Write-Host "https://git-scm.com/download/win" -ForegroundColor Cyan
    }
} else {
    Write-Host ""
    Write-Host "Ouverture de la page de téléchargement de Git..." -ForegroundColor Cyan
    Start-Process "https://git-scm.com/download/win"
    Write-Host ""
    Write-Host "Après l'installation:" -ForegroundColor Yellow
    Write-Host "1. Redémarrez PowerShell" -ForegroundColor Cyan
    Write-Host "2. Vérifiez avec: git --version" -ForegroundColor Cyan
    Write-Host "3. Relancez le script de synchronisation GitHub" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INSTALLATION TERMINÉE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
