# Diagnostic : Pourquoi Cursor s'execute en mode admin ?
# Executez ce script dans PowerShell (non-eleve)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "DIAGNOSTIC : Pourquoi Cursor est en mode admin ?" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verifier si le script lui-meme est en admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Write-Host "[1] Ce script PowerShell est-il en admin ?" -ForegroundColor Yellow
Write-Host "    Reponse: $isAdmin" -ForegroundColor $(if ($isAdmin) { "Red" } else { "Green" })
Write-Host ""

# 2. Trouver Cursor.exe
$cursorPaths = @(
    "C:\Program Files\cursor\Cursor.exe",
    "C:\Program Files\cursor\Cursor",
    "$env:LOCALAPPDATA\Programs\cursor\Cursor.exe",
    "C:\Program Files\Cursor\Cursor.exe"
)

$cursorExe = $null
foreach ($path in $cursorPaths) {
    if (Test-Path $path) {
        $cursorExe = $path
        break
    }
}

if (-not $cursorExe) {
    Write-Host "[ERREUR] Cursor.exe introuvable." -ForegroundColor Red
    exit 1
}

Write-Host "[2] Cursor.exe trouve :" -ForegroundColor Yellow
Write-Host "    $cursorExe" -ForegroundColor Green
Write-Host ""

# 3. Proprietes du fichier Cursor.exe
Write-Host "[3] Proprietes de Cursor.exe :" -ForegroundColor Yellow
$file = Get-Item $cursorExe -ErrorAction SilentlyContinue
if ($file) {
    Write-Host "    Chemin complet: $($file.FullName)" -ForegroundColor White
    Write-Host "    Date modification: $($file.LastWriteTime)" -ForegroundColor White
    Write-Host "    Taille: $([math]::Round($file.Length / 1MB, 2)) MB" -ForegroundColor White
}
Write-Host ""

# 4. Verifier le registre AppCompatFlags
Write-Host "[4] Registre AppCompatFlags (RUNASINVOKER) :" -ForegroundColor Yellow
$regPath = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
$regValue = Get-ItemProperty -Path $regPath -Name $cursorExe -ErrorAction SilentlyContinue
if ($regValue) {
    $value = $regValue.$cursorExe
    Write-Host "    Cle trouvee: OUI" -ForegroundColor Green
    Write-Host "    Valeur: $value" -ForegroundColor White
    if ($value -like "*RUNASINVOKER*") {
        Write-Host "    RUNASINVOKER est present" -ForegroundColor Green
    } else {
        Write-Host "    RUNASINVOKER est ABSENT" -ForegroundColor Red
    }
} else {
    Write-Host "    Cle trouvee: NON" -ForegroundColor Red
    Write-Host "    RUNASINVOKER n'est pas dans le registre" -ForegroundColor Red
}
Write-Host ""

# 5. Verifier les processus Cursor en cours
Write-Host "[5] Processus Cursor en cours d'execution :" -ForegroundColor Yellow
$cursorProcesses = Get-Process -Name "Cursor*" -ErrorAction SilentlyContinue
if ($cursorProcesses) {
    foreach ($proc in $cursorProcesses) {
        Write-Host "    PID $($proc.Id): $($proc.ProcessName)" -ForegroundColor White
        Write-Host "      Chemin: $($proc.Path)" -ForegroundColor Gray
        try {
            $procInfo = Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)" | Select-Object -First 1
            if ($procInfo) {
                $owner = $procInfo.GetOwner()
                Write-Host "      Utilisateur: $($owner.Domain)\$($owner.User)" -ForegroundColor Gray
                Write-Host "      Ligne de commande: $($procInfo.CommandLine)" -ForegroundColor Gray
            }
        } catch {
            Write-Host "      (impossible de recuperer les infos)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "    Aucun processus Cursor trouve" -ForegroundColor Yellow
}
Write-Host ""

# 6. Verifier les raccourcis dans le menu Demarrer
Write-Host "[6] Raccourcis dans le menu Demarrer :" -ForegroundColor Yellow
$startMenuPaths = @(
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
    "$env:ALLUSERSPROFILE\Microsoft\Windows\Start Menu\Programs"
)
$found = $false
foreach ($startPath in $startMenuPaths) {
    if (Test-Path $startPath) {
        $shortcuts = Get-ChildItem -Path $startPath -Recurse -Filter "*Cursor*.lnk" -ErrorAction SilentlyContinue
        foreach ($shortcut in $shortcuts) {
            $found = $true
            Write-Host "    Raccourci: $($shortcut.FullName)" -ForegroundColor White
            $shell = New-Object -ComObject WScript.Shell
            $link = $shell.CreateShortcut($shortcut.FullName)
            Write-Host "      Cible: $($link.TargetPath)" -ForegroundColor Gray
        }
    }
}
if (-not $found) {
    Write-Host "    Aucun raccourci trouve" -ForegroundColor Yellow
}
Write-Host ""

# Resume et recommandations
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "RESUME" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if ($regValue -and $regValue.$cursorExe -like "*RUNASINVOKER*") {
    Write-Host "[OK] RUNASINVOKER est dans le registre" -ForegroundColor Green
} else {
    Write-Host "[ACTION] RUNASINVOKER manquant - executez Forcer_Cursor_Sans_Admin_Registre.bat" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
