# Script: creer le depot GitHub Apps et pousser le code (compte Ameni-Novaprint-R)
# Usage: .\executer_sync_github.ps1
#        ou: $env:GITHUB_TOKEN = "ghp_xxx"; .\executer_sync_github.ps1

$ErrorActionPreference = "Stop"
$repoName = "Apps"
$githubUser = "Ameni-Novaprint-R"
$repoUrl = "https://github.com/$githubUser/$repoName.git"

# 1. Token
if (-not $env:GITHUB_TOKEN) {
    $token = Read-Host "Collez votre Personal Access Token (GitHub) pour $githubUser" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
    $env:GITHUB_TOKEN = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
}

if (-not $env:GITHUB_TOKEN) {
    Write-Host "Erreur: token manquant. Definissez GITHUB_TOKEN ou entrez-le quand demande." -ForegroundColor Red
    exit 1
}

# 2. Creer le depot sur GitHub (API)
Write-Host "Creation du depot $repoName sur GitHub..." -ForegroundColor Cyan
$body = @{
    name        = $repoName
    description = "Application web 22 projets"
    private     = $false
} | ConvertTo-Json

$headers = @{
    "Authorization" = "token $env:GITHUB_TOKEN"
    "Accept"        = "application/vnd.github.v3+json"
    "Content-Type"  = "application/json"
}

try {
    $result = Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Method Post -Headers $headers -Body $body
    Write-Host "Depot cree: $($result.html_url)" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host "Le depot existe deja, on continue avec le push." -ForegroundColor Yellow
    } else {
        Write-Host "API GitHub: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Verifiez que le token est valide pour le compte $githubUser (scope: repo)." -ForegroundColor Red
        exit 1
    }
}

# 3. Push
Set-Location $PSScriptRoot
$pushUrl = "https://${githubUser}:$env:GITHUB_TOKEN@github.com/${githubUser}/${repoName}.git"
Write-Host "Push vers $repoUrl ..." -ForegroundColor Cyan
& git push $pushUrl main 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors du push. Verifiez le token et que le depot existe." -ForegroundColor Red
    exit 1
}
& git branch --set-upstream-to=origin main 2>&1
& git remote set-url origin $repoUrl 2>&1

Write-Host "Termine. Projet sauvegarde sur: https://github.com/$githubUser/$repoName" -ForegroundColor Green
# Ne pas garder le token en memoire
Remove-Item Env:\GITHUB_TOKEN -ErrorAction SilentlyContinue
