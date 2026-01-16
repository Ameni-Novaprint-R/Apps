# Synchronisation directe avec GitHub

param(
    [string]$GitHubUsername = "",
    [string]$RepoName = ""
)

# Trouver Git
$gitPath = $null
$paths = @(
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files (x86)\Git\bin\git.exe",
    "$env:LOCALAPPDATA\Programs\Git\bin\git.exe",
    "C:\Program Files\Git\cmd\git.exe"
)

try {
    $result = Get-Command git -ErrorAction SilentlyContinue
    if ($result) { $gitPath = "git" }
} catch {}

if (-not $gitPath) {
    foreach ($p in $paths) {
        if (Test-Path $p) { $gitPath = $p; break }
    }
}

if (-not $gitPath) {
    Write-Host "Git non trouve. Redemarrez PowerShell apres l'installation." -ForegroundColor Red
    exit 1
}

Write-Host "Git: $gitPath" -ForegroundColor Green
& $gitPath --version
Write-Host ""

Set-Location "c:\Apps"

# Demander les infos si non fournies
if ([string]::IsNullOrWhiteSpace($GitHubUsername)) {
    $GitHubUsername = Read-Host "Nom d'utilisateur GitHub"
}
if ([string]::IsNullOrWhiteSpace($RepoName)) {
    $RepoName = Read-Host "Nom du depot GitHub"
}

# Configurer Git
Write-Host "Configuration Git..." -ForegroundColor Cyan
& $gitPath config user.email "ameni.compta@novaprint.tn"
& $gitPath config user.name "ameni.compta"

# Vérifier remote
$remote = & $gitPath remote get-url origin 2>$null
if ($remote) {
    Write-Host "Remote existant: $remote" -ForegroundColor Yellow
    & $gitPath remote remove origin
}

# Ajouter remote
$githubUrl = "https://github.com/$GitHubUsername/$RepoName.git"
Write-Host "Ajout remote: $githubUrl" -ForegroundColor Cyan
& $gitPath remote add origin $githubUrl

# Vérifier changements
$status = & $gitPath status --porcelain
if ($status) {
    Write-Host "Fichiers modifies detectes. Ajout..." -ForegroundColor Yellow
    & $gitPath add .
    $commitMsg = "Synchronisation initiale avec GitHub - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    & $gitPath commit -m $commitMsg
}

# Branche
$branch = & $gitPath branch --show-current
if (-not $branch) {
    & $gitPath checkout -b main
    $branch = "main"
}

Write-Host "Branche: $branch" -ForegroundColor Cyan

# Fetch si le dépôt existe
Write-Host "Verification du depot distant..." -ForegroundColor Cyan
try {
    & $gitPath fetch origin 2>&1 | Out-Null
    $remoteBranches = & $gitPath ls-remote --heads origin 2>$null
    if ($remoteBranches) {
        Write-Host "Fusion avec le depot distant..." -ForegroundColor Cyan
        & $gitPath merge origin/$branch --no-ff -m "Merge: Synchronisation GitHub" 2>&1 | Out-Null
    }
} catch {
    Write-Host "Le depot distant est vide ou n'existe pas encore." -ForegroundColor Yellow
}

# Push
Write-Host ""
Write-Host "Push vers GitHub (identifiants: ameni.compta@novaprint.tn)..." -ForegroundColor Cyan
& $gitPath push -u origin $branch

Write-Host ""
Write-Host "Synchronisation terminee!" -ForegroundColor Green
