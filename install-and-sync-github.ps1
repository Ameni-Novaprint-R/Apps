# Script pour installer Git (si nécessaire) et synchroniser avec GitHub

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INSTALLATION ET SYNCHRONISATION GITHUB" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si Git est installé
$gitPath = $null
$gitPaths = @(
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files (x86)\Git\bin\git.exe",
    "$env:LOCALAPPDATA\Programs\Git\bin\git.exe"
)

# Chercher Git dans le PATH
try {
    $result = Get-Command git -ErrorAction SilentlyContinue
    if ($result) {
        $gitPath = "git"
    }
} catch {
    # Continuer la recherche
}

# Chercher Git dans les emplacements standards
if (-not $gitPath) {
    foreach ($path in $gitPaths) {
        if (Test-Path $path) {
            $gitPath = $path
            break
        }
    }
}

if (-not $gitPath) {
    Write-Host "❌ Git n'est pas installé sur ce système." -ForegroundColor Red
    Write-Host ""
    Write-Host "Pour continuer, vous devez installer Git:" -ForegroundColor Yellow
    Write-Host "1. Téléchargez Git depuis: https://git-scm.com/download/win" -ForegroundColor Cyan
    Write-Host "2. Installez Git avec les options par défaut" -ForegroundColor Cyan
    Write-Host "3. Redémarrez PowerShell" -ForegroundColor Cyan
    Write-Host "4. Relancez ce script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "OU" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Si Git est installé mais pas dans le PATH:" -ForegroundColor Yellow
    Write-Host "1. Trouvez le chemin d'installation de Git" -ForegroundColor Cyan
    Write-Host "2. Ajoutez-le au PATH système" -ForegroundColor Cyan
    Write-Host ""
    
    # Demander si l'utilisateur veut ouvrir la page de téléchargement
    Write-Host "Voulez-vous ouvrir la page de téléchargement de Git? (O/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "O" -or $response -eq "o") {
        Start-Process "https://git-scm.com/download/win"
    }
    
    exit 1
}

Write-Host "✓ Git trouvé: $gitPath" -ForegroundColor Green
Write-Host ""

# Maintenant exécuter le script de synchronisation
Write-Host "Exécution du script de synchronisation..." -ForegroundColor Cyan
Write-Host ""

# Demander les informations nécessaires
Write-Host "Informations requises pour la synchronisation:" -ForegroundColor Yellow
Write-Host ""

Write-Host "Quel est votre nom d'utilisateur GitHub?" -ForegroundColor Yellow
Write-Host "(Si vous ne le connaissez pas, connectez-vous sur github.com et vérifiez votre profil)" -ForegroundColor Gray
$githubUsername = Read-Host

if ([string]::IsNullOrWhiteSpace($githubUsername)) {
    Write-Host "ERREUR: Le nom d'utilisateur GitHub est requis." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Quel est le nom du dépôt GitHub?" -ForegroundColor Yellow
Write-Host "(Le dépôt sera créé automatiquement s'il n'existe pas)" -ForegroundColor Gray
$repoName = Read-Host

if ([string]::IsNullOrWhiteSpace($repoName)) {
    Write-Host "ERREUR: Le nom du dépôt est requis." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Voulez-vous commiter automatiquement les fichiers modifiés? (O/N)" -ForegroundColor Yellow
$autoCommit = Read-Host
$autoCommitFlag = if ($autoCommit -eq "O" -or $autoCommit -eq "o") { "-AutoCommit" } else { "" }

Write-Host ""
Write-Host "Voulez-vous pousser automatiquement vers GitHub? (O/N)" -ForegroundColor Yellow
Write-Host "(Vous devrez entrer vos identifiants GitHub lors du push)" -ForegroundColor Gray
$autoPush = Read-Host
$autoPushFlag = if ($autoPush -eq "O" -or $autoPush -eq "o") { "-AutoPush" } else { "" }

# Exécuter le script de synchronisation
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LANCEMENT DE LA SYNCHRONISATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Construire les paramètres
$params = @{
    GitHubUsername = $githubUsername
    RepoName = $repoName
}

if ($autoCommitFlag) {
    $params['AutoCommit'] = $true
}

if ($autoPushFlag) {
    $params['AutoPush'] = $true
}

& "$PSScriptRoot\sync-github-auto.ps1" @params
