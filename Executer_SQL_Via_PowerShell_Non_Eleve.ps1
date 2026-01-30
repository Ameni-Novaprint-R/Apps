# Script PowerShell pour executer les scripts SQL via un processus non-eleve
# Utilise explorer.exe pour lancer un nouveau PowerShell sans elevation

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "EXECUTION DES SCRIPTS SQL VIA PROCESSUS NON-ELEVE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = "c:\Apps"
$script1 = Join-Path $scriptDir "creer_table_web_projets.py"
$script2 = Join-Path $scriptDir "creer_table_web_sections.py"

# Creer un script PowerShell temporaire qui execute les scripts Python
$tempPs1 = [System.IO.Path]::GetTempFileName() + ".ps1"

$psScriptContent = @"
`$ErrorActionPreference = 'Stop'
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "EXECUTION DES SCRIPTS SQL (PROCESSUS NON-ELEVE)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Push-Location '$scriptDir'

try {
    Write-Host "[DEBUT] creer_table_web_projets.py" -ForegroundColor Yellow
    `$output1 = python "$script1" 2>&1
    `$exitCode1 = `$LASTEXITCODE
    Write-Host `$output1
    if (`$exitCode1 -ne 0) {
        Write-Host "[ERREUR] creer_table_web_projets.py (code: `$exitCode1)" -ForegroundColor Red
        throw "Script 1 a echoue"
    }
    Write-Host "[SUCCES] creer_table_web_projets.py" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "[DEBUT] creer_table_web_sections.py" -ForegroundColor Yellow
    `$output2 = python "$script2" 2>&1
    `$exitCode2 = `$LASTEXITCODE
    Write-Host `$output2
    if (`$exitCode2 -ne 0) {
        Write-Host "[ERREUR] creer_table_web_sections.py (code: `$exitCode2)" -ForegroundColor Red
        throw "Script 2 a echoue"
    }
    Write-Host "[SUCCES] creer_table_web_sections.py" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "SUCCES: Tous les scripts ont ete executes." -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    
} catch {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "ERREUR: Certains scripts ont echoue." -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Cyan
    exit 1
} finally {
    Pop-Location
    Write-Host ""
    Write-Host "Appuyez sur une touche pour fermer cette fenetre..." -ForegroundColor Gray
    `$null = `$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
"@

Set-Content -Path $tempPs1 -Value $psScriptContent -Encoding UTF8

Write-Host "Lancement via explorer.exe pour creer un processus non-eleve..." -ForegroundColor Yellow
Write-Host ""

# Utiliser explorer.exe pour lancer PowerShell (explorer.exe cree un processus non-eleve)
# Format: explorer.exe "powershell.exe -ExecutionPolicy Bypass -File script.ps1"
$powershellCmd = "powershell.exe -ExecutionPolicy Bypass -NoExit -File `"$tempPs1`""
Start-Process -FilePath "explorer.exe" -ArgumentList $powershellCmd

Write-Host "Le script s'execute dans une nouvelle fenetre PowerShell (processus non-eleve)." -ForegroundColor Green
Write-Host "La fenetre PowerShell restera ouverte pour afficher les resultats." -ForegroundColor Green
Write-Host ""
Write-Host "Appuyez sur une touche pour fermer cette fenetre..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Nettoyer le fichier temporaire apres un delai
Start-Sleep -Seconds 2
Remove-Item $tempPs1 -ErrorAction SilentlyContinue
