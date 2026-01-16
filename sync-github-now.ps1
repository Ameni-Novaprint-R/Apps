# Script de synchronisation GitHub - Exécution immédiate

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SYNCHRONISATION GITHUB" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Trouver Git
$gitPath = $null
$gitPaths = @(
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files (x86)\Git\bin\git.exe",
    "$env:LOCALAPPDATA\Programs\Git\bin\git.exe",
    "C:\Program Files\Git\cmd\git.exe",
    "C:\Program Files (x86)\Git\cmd\git.exe"
)

# Chercher dans PATH
try {
    $result = Get-Command git -ErrorAction SilentlyContinue
    if ($result) {
        $gitPath = "git"
    }
} catch {
    # Continuer
}

# Chercher dans les emplacements standards
if (-not $gitPath) {
    foreach ($path in $gitPaths) {
        if (Test-Path $path) {
            $gitPath = $path
            break
        }
    }
}

# Si toujours pas trouvé, chercher récursivement dans Program Files
if (-not $gitPath) {
    Write-Host "Recherche de Git dans Program Files..." -ForegroundColor Yellow
    $found = Get-ChildItem "C:\Program Files" -Filter "git.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        $gitPath = $found.FullName
    }
}

if (-not $gitPath) {
    Write-Host "ERREUR: Git n'est pas trouve." -ForegroundColor Red
    Write-Host "Veuillez redemarrer PowerShell apres l'installation de Git." -ForegroundColor Yellow
    Write-Host "Ou ajoutez Git au PATH systeme." -ForegroundColor Yellow
    exit 1
}

Write-Host "Git trouve: $gitPath" -ForegroundColor Green
Write-Host "Version: $(& $gitPath --version)" -ForegroundColor Green
Write-Host ""

# Se placer dans le répertoire du projet
Set-Location "c:\Apps"

# Demander les informations
Write-Host "Informations requises:" -ForegroundColor Yellow
Write-Host ""

Write-Host "Nom d'utilisateur GitHub:" -ForegroundColor Cyan
Write-Host "(Exemple: ameni-compta ou ameni-compta-novaprint)" -ForegroundColor Gray
$githubUsername = Read-Host

if ([string]::IsNullOrWhiteSpace($githubUsername)) {
    Write-Host "ERREUR: Le nom d'utilisateur est requis." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Nom du depot GitHub:" -ForegroundColor Cyan
Write-Host "(Exemple: Apps ou novaprint-apps)" -ForegroundColor Gray
$repoName = Read-Host

if ([string]::IsNullOrWhiteSpace($repoName)) {
    Write-Host "ERREUR: Le nom du depot est requis." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Voulez-vous commiter automatiquement les fichiers modifies? (O/N)" -ForegroundColor Yellow
$autoCommit = Read-Host

Write-Host ""
Write-Host "Voulez-vous pousser automatiquement vers GitHub? (O/N)" -ForegroundColor Yellow
Write-Host "(Vous devrez entrer vos identifiants GitHub: ameni.compta@novaprint.tn)" -ForegroundColor Gray
$autoPush = Read-Host

# Exécuter le script de synchronisation
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LANCEMENT DE LA SYNCHRONISATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$params = @{
    GitHubUsername = $githubUsername
    RepoName = $repoName
}

if ($autoCommit -eq "O" -or $autoCommit -eq "o") {
    $params['AutoCommit'] = $true
}

if ($autoPush -eq "O" -or $autoPush -eq "o") {
    $params['AutoPush'] = $true
}

# Modifier temporairement le script pour utiliser le chemin complet de Git
$scriptContent = Get-Content "c:\Apps\sync-github-auto.ps1" -Raw
$scriptContent = $scriptContent -replace '& \$gitPath', "& '$gitPath'"
$tempScript = "$env:TEMP\sync-github-temp.ps1"
$scriptContent | Out-File $tempScript -Encoding UTF8

& $tempScript @params

# Nettoyer
Remove-Item $tempScript -ErrorAction SilentlyContinue
