# Verifier les proprietes du raccourci Cursor dans le menu Demarrer

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "VERIFICATION DU RACCOURCI CURSOR" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$shortcutPath = "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Cursor\Cursor - Raccourci.lnk"

if (Test-Path $shortcutPath) {
    Write-Host "[OK] Raccourci trouve: $shortcutPath" -ForegroundColor Green
    Write-Host ""
    
    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut($shortcutPath)
    
    Write-Host "Proprietes du raccourci:" -ForegroundColor Yellow
    Write-Host "  Cible: $($link.TargetPath)" -ForegroundColor White
    Write-Host "  Arguments: $($link.Arguments)" -ForegroundColor White
    Write-Host "  Repertoire de travail: $($link.WorkingDirectory)" -ForegroundColor White
    Write-Host ""
    
    # Verifier les proprietes de compatibilite du fichier cible
    $target = $link.TargetPath
    if (Test-Path $target) {
        Write-Host "Proprietes de compatibilite de $target :" -ForegroundColor Yellow
        Write-Host "  (Verifiez manuellement: clic droit sur le fichier -> Proprietes -> Onglet Compatibilite)" -ForegroundColor Gray
        Write-Host "  Recherche dans le registre..." -ForegroundColor Gray
        
        # Chercher dans le registre les proprietes de compatibilite
        $regPath = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
        $regValue = Get-ItemProperty -Path $regPath -Name $target -ErrorAction SilentlyContinue
        if ($regValue) {
            Write-Host "  [TROUVE] $($regValue.$target)" -ForegroundColor Green
        } else {
            Write-Host "  [NON TROUVE] Pas de propriete de compatibilite dans le registre" -ForegroundColor Yellow
        }
    }
    Write-Host ""
    
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "ACTION RECOMMANDEE" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Clic droit sur le raccourci -> Proprietes" -ForegroundColor White
    Write-Host "2. Onglet 'Raccourci' -> Bouton 'Avance...'" -ForegroundColor White
    Write-Host "3. Decocher 'Executer en tant qu'administrateur' si coché" -ForegroundColor White
    Write-Host "4. Appliquer -> OK" -ForegroundColor White
    Write-Host ""
    Write-Host "OU" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Utiliser UNIQUEMENT Lancer_Cursor_Sans_Admin.vbs pour lancer Cursor" -ForegroundColor Green
    Write-Host ""
    
} else {
    Write-Host "[ERREUR] Raccourci introuvable: $shortcutPath" -ForegroundColor Red
}

Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
