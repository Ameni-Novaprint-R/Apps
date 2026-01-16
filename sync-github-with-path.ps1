# Synchronisation GitHub avec ajout de Git au PATH

Write-Host "Ajout de Git au PATH de cette session..." -ForegroundColor Cyan

# Chemins possibles de Git
$gitPaths = @(
    "C:\Program Files\Git\bin",
    "C:\Program Files (x86)\Git\bin",
    "$env:LOCALAPPDATA\Programs\Git\bin",
    "C:\Program Files\Git\cmd",
    "C:\Program Files (x86)\Git\cmd"
)

$gitFound = $false
foreach ($gitDir in $gitPaths) {
    if (Test-Path $gitDir) {
        $gitExe = Join-Path $gitDir "git.exe"
        if (Test-Path $gitExe) {
            $env:Path += ";$gitDir"
            Write-Host "Git ajoute au PATH: $gitDir" -ForegroundColor Green
            $gitFound = $true
            break
        }
    }
}

if (-not $gitFound) {
    Write-Host "ERREUR: Git n'est pas trouve dans les emplacements standards." -ForegroundColor Red
    Write-Host ""
    Write-Host "Veuillez:" -ForegroundColor Yellow
    Write-Host "1. Redemarrer PowerShell (important!)" -ForegroundColor Cyan
    Write-Host "2. Ou trouver le chemin d'installation de Git" -ForegroundColor Cyan
    Write-Host "3. Relancer ce script" -ForegroundColor Cyan
    exit 1
}

# Vérifier que Git fonctionne maintenant
try {
    $version = git --version
    Write-Host "Git fonctionne: $version" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Git n'est toujours pas accessible." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Demarrage de la synchronisation..." -ForegroundColor Cyan
Write-Host ""

# Exécuter le script de synchronisation
& "$PSScriptRoot\sync-github-direct.ps1"
