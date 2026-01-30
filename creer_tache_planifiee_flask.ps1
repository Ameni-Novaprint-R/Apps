# Script PowerShell pour créer une tâche planifiée Windows qui démarre Flask automatiquement
# Nécessite des droits administrateur

$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "CREATION D'UNE TACHE PLANIFIEE POUR DEMARRER FLASK AUTOMATIQUEMENT" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier les droits administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERREUR] Ce script nécessite des droits administrateur." -ForegroundColor Red
    Write-Host "         Exécutez PowerShell en tant qu'administrateur." -ForegroundColor Yellow
    exit 1
}

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$taskName = "DemarrerFlaskAuto"
$scriptToRun = Join-Path $scriptPath "demarrer_flask_auto.ps1"

Write-Host "[INFO] Chemin du script: $scriptToRun" -ForegroundColor Green
Write-Host "[INFO] Nom de la tâche: $taskName" -ForegroundColor Green
Write-Host ""

# Vérifier si la tâche existe déjà
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[INFO] Une tâche avec ce nom existe déjà." -ForegroundColor Yellow
    $response = Read-Host "Voulez-vous la supprimer et en créer une nouvelle? (O/N)"
    if ($response -eq "O" -or $response -eq "o") {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "[INFO] Tâche existante supprimée." -ForegroundColor Green
    } else {
        Write-Host "[INFO] Opération annulée." -ForegroundColor Yellow
        exit 0
    }
}

# Demander le type de déclenchement
Write-Host ""
Write-Host "Choisissez le type de déclenchement:" -ForegroundColor Cyan
Write-Host "1. Au démarrage de Windows"
Write-Host "2. À l'ouverture de session"
Write-Host "3. À une heure spécifique (tous les jours)"
Write-Host ""
$choice = Read-Host "Votre choix (1-3)"

$trigger = $null
switch ($choice) {
    "1" {
        $trigger = New-ScheduledTaskTrigger -AtStartup
        Write-Host "[INFO] Tâche configurée pour démarrer au démarrage de Windows." -ForegroundColor Green
    }
    "2" {
        $trigger = New-ScheduledTaskTrigger -AtLogOn
        Write-Host "[INFO] Tâche configurée pour démarrer à l'ouverture de session." -ForegroundColor Green
    }
    "3" {
        $hour = Read-Host "Heure (0-23)"
        $minute = Read-Host "Minute (0-59)"
        $trigger = New-ScheduledTaskTrigger -Daily -At "$($hour):$($minute)"
        Write-Host "[INFO] Tâche configurée pour démarrer tous les jours à $($hour):$($minute)." -ForegroundColor Green
    }
    default {
        Write-Host "[ERREUR] Choix invalide." -ForegroundColor Red
        exit 1
    }
}

# Créer l'action
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$scriptToRun`"" `
    -WorkingDirectory $scriptPath

# Créer les paramètres
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Créer le principal (exécuter avec les droits de l'utilisateur actuel)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Enregistrer la tâche
try {
    Register-ScheduledTask -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Démarre Flask automatiquement" | Out-Null
    
    Write-Host ""
    Write-Host "[SUCCES] Tâche planifiée créée avec succès!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Pour tester la tâche immédiatement:" -ForegroundColor Cyan
    Write-Host "  Start-ScheduledTask -TaskName `"$taskName`"" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Pour voir les tâches planifiées:" -ForegroundColor Cyan
    Write-Host "  Get-ScheduledTask -TaskName `"$taskName`"" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Pour supprimer la tâche:" -ForegroundColor Cyan
    Write-Host "  Unregister-ScheduledTask -TaskName `"$taskName`" -Confirm:`$false" -ForegroundColor Yellow
    
} catch {
    Write-Host "[ERREUR] Impossible de créer la tâche planifiée: $_" -ForegroundColor Red
    exit 1
}
