# Script de synchronisation NON DESTRUCTIVE avec GitHub
# Aucune suppression, aucun --force, préservation totale du code existant

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
    Write-Host "Ou ajouter Git au PATH système." -ForegroundColor Yellow
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
    Write-Host "Voulez-vous le remplacer par le nouveau compte GitHub? (O/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -ne "O" -and $response -ne "o") {
        Write-Host "Opération annulée." -ForegroundColor Red
        exit 0
    }
    & $gitPath remote remove origin
}

# Configurer Git avec le nouveau compte
Write-Host ""
Write-Host "Configuration de Git avec le nouveau compte..." -ForegroundColor Cyan
& $gitPath config user.email "ameni.compta@novaprint.tn"
& $gitPath config user.name "ameni.compta"

# Demander le nom d'utilisateur GitHub
Write-Host ""
Write-Host "Quel est votre nom d'utilisateur GitHub? (ex: ameni-compta ou ameni-compta-novaprint)" -ForegroundColor Yellow
$githubUsername = Read-Host

if ([string]::IsNullOrWhiteSpace($githubUsername)) {
    Write-Host "ERREUR: Le nom d'utilisateur GitHub est requis." -ForegroundColor Red
    exit 1
}

# Demander le nom du dépôt GitHub
Write-Host ""
Write-Host "Quel est le nom du dépôt GitHub? (ex: Apps ou novaprint-apps)" -ForegroundColor Yellow
$repoName = Read-Host

if ([string]::IsNullOrWhiteSpace($repoName)) {
    Write-Host "ERREUR: Le nom du dépôt est requis." -ForegroundColor Red
    exit 1
}

# Ajouter le remote GitHub
$githubUrl = "https://github.com/$githubUsername/$repoName.git"
Write-Host ""
Write-Host "Ajout du remote GitHub: $githubUrl" -ForegroundColor Cyan
& $gitPath remote add origin $githubUrl

# Vérifier s'il y a des changements non commités
$status = & $gitPath status --porcelain
if ($status) {
    Write-Host ""
    Write-Host "ATTENTION: Il y a des fichiers modifiés non commités." -ForegroundColor Yellow
    Write-Host "Voulez-vous les commiter avant de synchroniser? (O/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "O" -or $response -eq "o") {
        Write-Host ""
        Write-Host "Ajout de tous les fichiers..." -ForegroundColor Cyan
        & $gitPath add .
        
        Write-Host "Création du commit..." -ForegroundColor Cyan
        $commitMessage = "Synchronisation initiale avec GitHub - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        & $gitPath commit -m $commitMessage
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
        
        # Vérifier s'il y a des conflits potentiels
        $localCommits = & $gitPath log --oneline -10 2>$null
        $remoteCommits = & $gitPath log --oneline origin/$currentBranch -10 2>$null
        
        if ($localCommits -and $remoteCommits) {
            Write-Host ""
            Write-Host "ATTENTION: Des commits existent à la fois localement et sur GitHub." -ForegroundColor Yellow
            Write-Host "Voulez-vous créer une branche de sauvegarde avant la fusion? (O/N)" -ForegroundColor Yellow
            $response = Read-Host
            if ($response -eq "O" -or $response -eq "o") {
                $backupBranch = "backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
                Write-Host "Création de la branche de sauvegarde: $backupBranch" -ForegroundColor Cyan
                & $gitPath branch $backupBranch
            }
        }
        
        # Merge sans fast-forward pour préserver l'historique
        Write-Host ""
        Write-Host "Fusion avec le dépôt distant (merge --no-ff)..." -ForegroundColor Cyan
        try {
            & $gitPath merge origin/$currentBranch --no-ff --no-edit -m "Merge: Synchronisation avec GitHub - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
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
    Write-Host ""
    Write-Host "Voulez-vous continuer avec le push? (O/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -ne "O" -and $response -ne "o") {
        Write-Host "Opération annulée." -ForegroundColor Red
        exit 0
    }
}

# Push NON DESTRUCTIF (sans --force)
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PUSH VERS GITHUB (NON DESTRUCTIF)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANT: Aucun --force ne sera utilisé." -ForegroundColor Yellow
Write-Host "Tous les fichiers et l'historique seront préservés." -ForegroundColor Green
Write-Host ""

# Demander confirmation
Write-Host "Voulez-vous pousser vers GitHub maintenant? (O/N)" -ForegroundColor Yellow
$response = Read-Host

if ($response -eq "O" -or $response -eq "o") {
    Write-Host ""
    Write-Host "Push vers GitHub..." -ForegroundColor Cyan
    
    # Push avec set-upstream (sans --force)
    try {
        & $gitPath push -u origin $currentBranch
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
        Write-Host ""
        Write-Host "Si le dépôt distant a des commits que vous n'avez pas localement," -ForegroundColor Yellow
        Write-Host "vous devrez d'abord faire un merge (voir ci-dessus)." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "Push annulé. Vous pouvez le faire manuellement plus tard avec:" -ForegroundColor Yellow
    Write-Host "  git push -u origin $currentBranch" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SYNCHRONISATION TERMINÉE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
