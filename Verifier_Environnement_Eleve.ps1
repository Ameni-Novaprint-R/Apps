# Verifier si l'environnement est eleve (processus parents en admin)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "VERIFICATION DE L'ENVIRONNEMENT ELEVE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verifier PowerShell actuel
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Write-Host "[1] Ce PowerShell est-il en admin ?" -ForegroundColor Yellow
Write-Host "    Reponse: $isAdmin" -ForegroundColor $(if ($isAdmin) { "Red" } else { "Green" })
Write-Host ""

# 2. Verifier l'Explorateur Windows
Write-Host "[2] Explorateur Windows (explorer.exe) :" -ForegroundColor Yellow
$explorer = Get-Process -Name "explorer" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($explorer) {
    Write-Host "    PID: $($explorer.Id)" -ForegroundColor White
    try {
        $procInfo = Get-WmiObject Win32_Process -Filter "ProcessId = $($explorer.Id)" | Select-Object -First 1
        if ($procInfo) {
            $owner = $procInfo.GetOwner()
            Write-Host "    Utilisateur: $($owner.Domain)\$($owner.User)" -ForegroundColor White
            Write-Host "    Si l'Explorateur est en admin, tout ce que vous ouvrez peut etre eleve" -ForegroundColor $(if ($isAdmin) { "Red" } else { "Yellow" })
        }
    } catch {
        Write-Host "    (impossible de recuperer les infos)" -ForegroundColor Yellow
    }
} else {
    Write-Host "    Explorateur non trouve" -ForegroundColor Yellow
}
Write-Host ""

# 3. Verifier le processus parent de ce PowerShell
Write-Host "[3] Processus parent de ce PowerShell :" -ForegroundColor Yellow
$currentPID = $PID
try {
    $currentProc = Get-WmiObject Win32_Process -Filter "ProcessId = $currentPID" | Select-Object -First 1
    if ($currentProc -and $currentProc.ParentProcessId) {
        $parentPID = $currentProc.ParentProcessId
        $parentProc = Get-WmiObject Win32_Process -Filter "ProcessId = $parentPID" | Select-Object -First 1
        if ($parentProc) {
            Write-Host "    Parent PID: $parentPID" -ForegroundColor White
            Write-Host "    Nom: $($parentProc.Name)" -ForegroundColor White
            Write-Host "    Ligne de commande: $($parentProc.CommandLine)" -ForegroundColor Gray
            if ($parentProc.Name -eq "explorer.exe") {
                Write-Host "    [INFO] Ce PowerShell a ete lance depuis l'Explorateur" -ForegroundColor Yellow
            }
        }
    }
} catch {
    Write-Host "    (impossible de recuperer le parent)" -ForegroundColor Yellow
}
Write-Host ""

# 4. Verifier les processus Cursor en cours
Write-Host "[4] Processus Cursor en cours :" -ForegroundColor Yellow
$cursorProcesses = Get-Process -Name "Cursor*" -ErrorAction SilentlyContinue
if ($cursorProcesses) {
    foreach ($proc in $cursorProcesses) {
        Write-Host "    PID $($proc.Id): $($proc.ProcessName)" -ForegroundColor White
        try {
            $procInfo = Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)" | Select-Object -First 1
            if ($procInfo) {
                $owner = $procInfo.GetOwner()
                Write-Host "      Utilisateur: $($owner.Domain)\$($owner.User)" -ForegroundColor Gray
                Write-Host "      Parent PID: $($procInfo.ParentProcessId)" -ForegroundColor Gray
                $parent = Get-WmiObject Win32_Process -Filter "ProcessId = $($procInfo.ParentProcessId)" -ErrorAction SilentlyContinue
                if ($parent) {
                    Write-Host "      Parent: $($parent.Name)" -ForegroundColor Gray
                }
            }
        } catch {
            Write-Host "      (impossible de recuperer les infos)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "    Aucun processus Cursor trouve" -ForegroundColor Yellow
}
Write-Host ""

# Resume
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "RESUME" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if ($isAdmin) {
    Write-Host "[ATTENTION] Ce PowerShell est en mode admin" -ForegroundColor Red
    Write-Host "  -> Tout ce que vous lancez depuis ici peut etre eleve" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "SOLUTION:" -ForegroundColor Yellow
    Write-Host "  1. Fermer ce PowerShell" -ForegroundColor White
    Write-Host "  2. Ouvrir un NOUVEAU PowerShell SANS 'Executer en tant qu'administrateur'" -ForegroundColor White
    Write-Host "  3. Depuis ce nouveau PowerShell, lancer Cursor via le .vbs" -ForegroundColor White
} else {
    Write-Host "[OK] Ce PowerShell n'est PAS en mode admin" -ForegroundColor Green
    Write-Host "  -> L'environnement semble correct" -ForegroundColor Green
}

Write-Host ""
Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
