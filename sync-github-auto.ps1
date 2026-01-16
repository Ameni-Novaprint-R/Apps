# Script de synchronisation NON DESTRUCTIVE avec GitHub - Version Automatique
# Usage: .\sync-github-auto.ps1 -GitHubUsername "username" -RepoName "repo-name"

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubUsername,
    
    [Parameter(Mandatory=$true)]
    [string]$RepoName,
    
    [switch]$AutoCommit = $false,
    [switch]$AutoPush = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SYNCHRONISATION GITHUB NON DESTRUCTIVE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si Git est installé
$gitPath = $null
$gitPaths = @(
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files (x86)\Git\bin\git.exe",
    "$env:LOCALAPPDATA\Programs\Git\bin\git.exe",
    "git"  # Si dans PATH
)

foreach ($path in $gitPaths) {
    try {
        if ($path -eq "git") {
            $result = Get-Command git -ErrorAction SilentlyContinue
            if ($result) {
                $gitPath = "git"
                break
            }
        } else {
            if (Test-Path $path) {
                $gitPath = $path
                break
            }
        }
    } catch {
        continue
    }
}

if (-not $gitPath) {
    Write-Host "ERREUR: Git n'est pas installé ou pas trouvé dans le PATH." -ForegroundColor Red
    Write-Host "Veuillez installer Git depuis https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Git trouvé: $gitPath" -ForegroundColor Green
Write-Host ""

# Se placer dans le répertoire du projet
$projectDir = "c:\Apps"
Set-Location $projectDir

Write-Host "Répertoire de travail: $projectDir" -ForegroundColor Cyan
Write-Host ""

# Vérifier l'état du dépôt
Write-Host "Vérification de l'état du dépôt Git..." -ForegroundColor Cyan
& $gitPath status --short

# Vérifier si un remote GitHub existe déjà
$remoteUrl = & $gitPath remote get-url origin 2>$null

if ($remoteUrl) {
    Write-Host ""
    Write-Host "Remote existant: $remoteUrl" -ForegroundColor Yellow
    Write-Host "Suppression du remote existant..." -ForegroundColor Cyan
    & $gitPath remote remove origin
}

# Configurer Git avec le nouveau compte
Write-Host ""
Write-Host "Configuration de Git avec le nouveau compte..." -ForegroundColor Cyan
& $gitPath config user.email "ameni.compta@novaprint.tn"
& $gitPath config user.name "ameni.compta"

# Ajouter le remote GitHub
$githubUrl = "https://github.com/$GitHubUsername/$RepoName.git"
Write-Host ""
Write-Host "Ajout du remote GitHub: $githubUrl" -ForegroundColor Cyan
& $gitPath remote add origin $githubUrl

# Vérifier s'il y a des changements non commités
$status = & $gitPath status --porcelain
if ($status) {
    Write-Host ""
    Write-Host "Fichiers modifiés détectés." -ForegroundColor Yellow
    if ($AutoCommit) {
        Write-Host "Ajout de tous les fichiers..." -ForegroundColor Cyan
        & $gitPath add .
        
        Write-Host "Création du commit..." -ForegroundColor Cyan
        $commitMessage = "Synchronisation initiale avec GitHub - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        & $gitPath commit -m $commitMessage
    } else {
        Write-Host "ATTENTION: Il y a des fichiers modifiés non commités." -ForegroundColor Yellow
        Write-Host "Utilisez -AutoCommit pour les commiter automatiquement." -ForegroundColor Yellow
    }
}

# Vérifier la branche actuelle
$currentBranch = & $gitPath branch --show-current
if (-not $currentBranch) {
    # Pas de branche, créer main
    Write-Host ""
    Write-Host "Création de la branche 'main'..." -ForegroundColor Cyan
    & $gitPath checkout -b main
    $currentBranch = "main"
}

Write-Host ""
Write-Host "Branche actuelle: $currentBranch" -ForegroundColor Cyan

# Vérifier si le dépôt distant existe et a des commits
Write-Host ""
Write-Host "Vérification du dépôt distant..." -ForegroundColor Cyan
try {
    & $gitPath ls-remote origin --heads 2>&1 | Out-Null
    $remoteExists = $true
} catch {
    $remoteExists = $false
}

if ($remoteExists) {
    Write-Host "Le dépôt distant existe." -ForegroundColor Green
    
    # Récupérer les informations du dépôt distant
    $remoteBranches = & $gitPath ls-remote --heads origin 2>$null
    
    if ($remoteBranches) {
        Write-Host ""
        Write-Host "Le dépôt distant contient déjà des branches." -ForegroundColor Yellow
        Write-Host "Stratégie NON DESTRUCTIVE:" -ForegroundColor Cyan
        Write-Host "1. Récupération des données distantes (fetch)" -ForegroundColor Cyan
        Write-Host "2. Fusion (merge) sans écrasement" -ForegroundColor Cyan
        Write-Host ""
        
        # Fetch
        Write-Host "Récupération des données distantes (fetch)..." -ForegroundColor Cyan
        & $gitPath fetch origin
        
        # Créer une branche de sauvegarde
        $backupBranch = "backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Write-Host "Création de la branche de sauvegarde: $backupBranch" -ForegroundColor Cyan
        & $gitPath branch $backupBranch
        
        # Merge sans fast-forward pour préserver l'historique
        Write-Host ""
        Write-Host "Fusion avec le dépôt distant (merge --no-ff)..." -ForegroundColor Cyan
        try {
            & $gitPath merge origin/$currentBranch --no-ff --no-edit -m "Merge: Synchronisation avec GitHub - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" 2>&1 | Out-Null
            Write-Host "✓ Fusion réussie" -ForegroundColor Green
        } catch {
            Write-Host "⚠ Conflits détectés. Résolution manuelle requise." -ForegroundColor Yellow
            Write-Host "Les fichiers en conflit sont préservés. Résolvez-les manuellement puis:" -ForegroundColor Yellow
            Write-Host "  git add ." -ForegroundColor Cyan
            Write-Host "  git commit" -ForegroundColor Cyan
            exit 1
        }
    } else {
        Write-Host "Le dépôt distant est vide." -ForegroundColor Green
    }
} else {
    Write-Host "Le dépôt distant n'existe pas encore ou n'est pas accessible." -ForegroundColor Yellow
    Write-Host "Assurez-vous que le dépôt GitHub existe et que vous avez les droits d'accès." -ForegroundColor Yellow
}

# Push NON DESTRUCTIF (sans --force)
if ($AutoPush) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "PUSH VERS GITHUB (NON DESTRUCTIF)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Aucun --force ne sera utilisé." -ForegroundColor Yellow
    Write-Host "Tous les fichiers et l'historique seront préservés." -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Push vers GitHub..." -ForegroundColor Cyan
    
    # Push avec set-upstream (sans --force)
    try {
        & $gitPath push -u origin $currentBranch 2>&1
        Write-Host ""
        Write-Host "✓ Synchronisation réussie!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Le dépôt a été synchronisé avec GitHub de manière non destructive." -ForegroundColor Green
        Write-Host "Tous les fichiers et l'historique ont été préservés." -ForegroundColor Green
    } catch {
        Write-Host ""
        Write-Host "ERREUR lors du push." -ForegroundColor Red
        Write-Host "Vérifiez:" -ForegroundColor Yellow
        Write-Host "  1. Que le dépôt GitHub existe" -ForegroundColor Yellow
        Write-Host "  2. Que vous avez les droits d'accès" -ForegroundColor Yellow
        Write-Host "  3. Que les identifiants sont corrects" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "Pour pousser vers GitHub, exécutez:" -ForegroundColor Yellow
    Write-Host "  git push -u origin $currentBranch" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Ou relancez ce script avec -AutoPush" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SYNCHRONISATION TERMINÉE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
