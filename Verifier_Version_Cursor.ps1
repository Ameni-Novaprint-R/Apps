# Verifier la version de Cursor et les changements recents

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "VERSION DE CURSOR ET INFORMATIONS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$cursorExe = "C:\Program Files\cursor\Cursor.exe"
if (-not (Test-Path $cursorExe)) {
    $cursorExe = "$env:LOCALAPPDATA\Programs\cursor\Cursor.exe"
}

if (Test-Path $cursorExe) {
    $file = Get-Item $cursorExe
    Write-Host "Cursor.exe :" -ForegroundColor Yellow
    Write-Host "  Chemin: $($file.FullName)" -ForegroundColor White
    Write-Host "  Date modification: $($file.LastWriteTime)" -ForegroundColor White
    Write-Host "  Taille: $([math]::Round($file.Length / 1MB, 2)) MB" -ForegroundColor White
    Write-Host ""
}

# Lire package.json pour la version
$packageJson = "C:\Program Files\cursor\resources\app\package.json"
if (Test-Path $packageJson) {
    try {
        $pkg = Get-Content $packageJson | ConvertFrom-Json
        Write-Host "Version Cursor (package.json):" -ForegroundColor Yellow
        Write-Host "  Version: $($pkg.version)" -ForegroundColor White
        Write-Host ""
    } catch {
        Write-Host "  (impossible de lire package.json)" -ForegroundColor Yellow
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "INFORMATIONS SUR LE PROBLEME" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Si l'execution des SQL fonctionnait AVANT la mise a jour," -ForegroundColor Yellow
Write-Host "et ne fonctionne PLUS APRES, c'est probablement un changement" -ForegroundColor Yellow
Write-Host "dans la nouvelle version de Cursor." -ForegroundColor Yellow
Write-Host ""
Write-Host "Les versions recentes (2.1.50+) ont introduit des restrictions" -ForegroundColor White
Write-Host "plus strictes sur l'execution de commandes quand le processus" -ForegroundColor White
Write-Host "est detecte comme eleve, meme avec chat.sandboxEnabled: false." -ForegroundColor White
Write-Host ""
Write-Host "SOLUTIONS POSSIBLES:" -ForegroundColor Cyan
Write-Host "  1. Desinstaller la mise a jour et revenir a une version anterieure" -ForegroundColor White
Write-Host "  2. Utiliser la route web (fonctionne toujours)" -ForegroundColor White
Write-Host "  3. Attendre un correctif de Cursor" -ForegroundColor White
Write-Host ""

Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
