# Push final vers GitHub avec gestion de l'authentification

$gitPath = "C:\Program Files\Git\bin\git.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SYNCHRONISATION FINALE AVEC GITHUB" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "c:\Apps"

# Vérifier l'état
Write-Host "Etat du depot:" -ForegroundColor Cyan
& $gitPath status -sb
Write-Host ""

# Vérifier les commits
$commits = & $gitPath log origin/main..HEAD --oneline 2>$null
if ($commits) {
    Write-Host "Commits a pousser:" -ForegroundColor Yellow
    $commits | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    Write-Host ""
} else {
    Write-Host "Aucun commit a pousser ou la branche distante n'existe pas encore." -ForegroundColor Yellow
    Write-Host ""
}

# Instructions pour l'authentification
Write-Host "AUTHENTIFICATION GITHUB:" -ForegroundColor Yellow
Write-Host ""
Write-Host "GitHub n'accepte plus les mots de passe en ligne de commande." -ForegroundColor Yellow
Write-Host "Options:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Option 1: Personal Access Token (RECOMMANDE)" -ForegroundColor Green
Write-Host "  1. Allez sur https://github.com/settings/tokens" -ForegroundColor Cyan
Write-Host "  2. Cliquez sur 'Generate new token (classic)'" -ForegroundColor Cyan
Write-Host "  3. Donnez un nom (ex: 'Apps Sync')" -ForegroundColor Cyan
Write-Host "  4. Cochez 'repo' pour les permissions" -ForegroundColor Cyan
Write-Host "  5. Cliquez sur 'Generate token'" -ForegroundColor Cyan
Write-Host "  6. Copiez le token (vous ne le reverrez plus!)" -ForegroundColor Cyan
Write-Host "  7. Utilisez ce token comme mot de passe lors du push" -ForegroundColor Cyan
Write-Host ""
Write-Host "Option 2: Git Credential Manager" -ForegroundColor Green
Write-Host "  Git Credential Manager devrait s'ouvrir automatiquement" -ForegroundColor Cyan
Write-Host "  Utilisez vos identifiants GitHub" -ForegroundColor Cyan
Write-Host ""

$choice = Read-Host "Voulez-vous continuer avec le push maintenant? (O/N)"

if ($choice -ne "O" -and $choice -ne "o") {
    Write-Host "Push annule." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Push vers GitHub..." -ForegroundColor Cyan
Write-Host ""

# Push
$branch = & $gitPath branch --show-current
if (-not $branch) {
    $branch = "main"
}

try {
    & $gitPath push -u origin $branch
    Write-Host ""
    Write-Host "Push reussi!" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "Erreur lors du push." -ForegroundColor Red
    Write-Host "Si l'authentification a echoue:" -ForegroundColor Yellow
    Write-Host "  1. Utilisez un Personal Access Token comme mot de passe" -ForegroundColor Cyan
    Write-Host "  2. Ou configurez Git Credential Manager" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Pour creer un token: https://github.com/settings/tokens" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Verification finale..." -ForegroundColor Cyan
& $gitPath status -sb

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
