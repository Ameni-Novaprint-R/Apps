# Push vers GitHub avec authentification

$gitPath = "C:\Program Files\Git\bin\git.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PUSH VERS GITHUB" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "c:\Apps"

# Vérifier le remote
$remote = & $gitPath remote get-url origin
Write-Host "Remote: $remote" -ForegroundColor Cyan
Write-Host ""

# Vérifier les commits à pousser
$branch = & $gitPath branch --show-current
Write-Host "Branche: $branch" -ForegroundColor Cyan

# Vérifier si le tracking est configuré
$tracking = & $gitPath branch -vv | Select-String $branch
Write-Host "Tracking: $tracking" -ForegroundColor Cyan
Write-Host ""

# Configurer le tracking si nécessaire
Write-Host "Configuration du tracking..." -ForegroundColor Yellow
& $gitPath branch --set-upstream-to=origin/$branch $branch 2>&1 | Out-Null

Write-Host ""
Write-Host "Push vers GitHub..." -ForegroundColor Cyan
Write-Host "Identifiants requis:" -ForegroundColor Yellow
Write-Host "  Username: ameni.compta@novaprint.tn" -ForegroundColor Gray
Write-Host "  Password: @menI123**" -ForegroundColor Gray
Write-Host ""

# Push avec les identifiants
# Note: Git demandera les identifiants via une fenêtre ou en ligne de commande
& $gitPath push -u origin $branch

Write-Host ""
Write-Host "Verification de l'etat..." -ForegroundColor Cyan
& $gitPath status -sb

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TERMINE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
