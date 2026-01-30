#!/usr/bin/env powershell
# -*- coding: utf-8 -*-
# Script pour arrêter toutes les instances Flask (version avec droits administrateur)

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "ATTENTION: Droits administrateur requis!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Ce script doit etre execute en tant qu'administrateur pour pouvoir" -ForegroundColor Yellow
    Write-Host "arreter tous les processus Python." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Pour executer en tant qu'administrateur:" -ForegroundColor Cyan
    Write-Host "1. Clic droit sur PowerShell" -ForegroundColor White
    Write-Host "2. Selectionner 'Executer en tant qu'administrateur'" -ForegroundColor White
    Write-Host "3. Naviguer vers C:\Apps" -ForegroundColor White
    Write-Host "4. Executer: .\arreter_toutes_instances_flask_admin.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Ou utilisez le script normal: .\arreter_toutes_instances_flask.ps1" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ARRET DE TOUTES LES INSTANCES FLASK" -ForegroundColor Cyan
Write-Host "(Mode Administrateur)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Étape 1: Trouver tous les processus Python et leurs processus parents
Write-Host "[1/4] Recherche des processus Python..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "   Trouve $($pythonProcesses.Count) processus Python" -ForegroundColor White
    
    # Afficher les détails de chaque processus et trouver les processus parents
    $parentPids = @()
    foreach ($proc in $pythonProcesses) {
        try {
            $procInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction Stop
            $cmdLine = $procInfo.CommandLine
            $parentPid = $procInfo.ParentProcessId
            
            Write-Host "   - PID $($proc.Id): $($cmdLine)" -ForegroundColor Gray
            
            # Vérifier si c'est Flask (app.py, run_flask_with_watchdog.py, etc.)
            if ($cmdLine -match 'app\.py|run_flask|flask|watchdog|wsgi\.py') {
                Write-Host "     -> Instance Flask detectee!" -ForegroundColor Red
            }
            
            # Enregistrer le PID parent si ce n'est pas déjà dans la liste
            if ($parentPid -and $parentPid -notin $parentPids) {
                $parentPids += $parentPid
                try {
                    $parentProc = Get-Process -Id $parentPid -ErrorAction SilentlyContinue
                    Write-Host "     -> Processus parent: PID $parentPid ($($parentProc.ProcessName))" -ForegroundColor Yellow
                } catch {
                    Write-Host "     -> Processus parent: PID $parentPid (inconnu)" -ForegroundColor Yellow
                }
            }
        } catch {
            Write-Host "   - PID $($proc.Id): $($proc.ProcessName)" -ForegroundColor Gray
        }
    }
    
    # Si on trouve des processus parents, proposer de les arrêter aussi
    if ($parentPids.Count -gt 0) {
        Write-Host ""
        Write-Host "   ATTENTION: Processus parents detectes qui peuvent recreer les processus Python!" -ForegroundColor Yellow
        Write-Host "   PIDs parents: $($parentPids -join ', ')" -ForegroundColor Yellow
        Write-Host "   Ces processus seront arretes apres les processus Python." -ForegroundColor Cyan
    }
} else {
    Write-Host "   Aucun processus Python trouve" -ForegroundColor Green
}

Write-Host ""

# Étape 2: Arrêter tous les processus Python (avec boucle pour gérer les nouveaux processus)
Write-Host "[2/4] Arret de tous les processus Python..." -ForegroundColor Yellow
$maxIterations = 5
$iteration = 0
$totalStopped = 0

while ($iteration -lt $maxIterations) {
    $currentProcesses = Get-Process python -ErrorAction SilentlyContinue
    if (-not $currentProcesses) {
        Write-Host "   Aucun processus Python restant" -ForegroundColor Green
        break
    }
    
    if ($iteration -gt 0) {
        Write-Host "   Iteration $($iteration + 1): Nouveaux processus detectes ($($currentProcesses.Count))" -ForegroundColor Yellow
    }
    
    $stopped = 0
    foreach ($proc in $currentProcesses) {
        try {
            # Vérifier que le processus existe encore avant d'essayer de l'arrêter
            $procStillExists = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
            if (-not $procStillExists) {
                Write-Host "   Processus PID $($proc.Id) deja arrete" -ForegroundColor Gray
                continue
            }
            
            Write-Host "   Arret du processus PID $($proc.Id)..." -ForegroundColor White
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "   -> Processus $($proc.Id) arrete" -ForegroundColor Green
            $stopped++
            $totalStopped++
        } catch {
            # Le processus peut avoir disparu entre temps
            if ($_.Exception.Message -match "Impossible de trouver|Cannot find") {
                Write-Host "   -> Processus PID $($proc.Id) deja arrete" -ForegroundColor Gray
            } else {
                Write-Host "   -> Erreur lors de l'arret du processus $($proc.Id) : ${_}" -ForegroundColor Red
            }
        }
    }
    
    Start-Sleep -Seconds 2
    $iteration++
}

if ($totalStopped -gt 0) {
    Write-Host "   Total: $totalStopped processus arrete(s)" -ForegroundColor Green
} else {
    Write-Host "   Aucun processus a arreter" -ForegroundColor Green
}

Write-Host ""

# Étape 2.5: Arrêter les processus parents si identifiés
if ($parentPids -and $parentPids.Count -gt 0) {
    Write-Host "[2.5/4] Arret des processus parents..." -ForegroundColor Yellow
    foreach ($parentPid in $parentPids) {
        try {
            $parentProc = Get-Process -Id $parentPid -ErrorAction SilentlyContinue
            if ($parentProc) {
                Write-Host "   Arret du processus parent PID $parentPid ($($parentProc.ProcessName))..." -ForegroundColor White
                # Vérifier si c'est PowerShell ou CMD - on ne veut pas arrêter notre propre session
                if ($parentProc.ProcessName -match 'powershell|cmd|pwsh') {
                    Write-Host "     -> Processus $parentPid ignore (session PowerShell/CMD active)" -ForegroundColor Gray
                } else {
                    Stop-Process -Id $parentPid -Force -ErrorAction Stop
                    Write-Host "     -> Processus parent $parentPid arrete" -ForegroundColor Green
                }
            } else {
                Write-Host "   Processus parent PID $parentPid deja arrete" -ForegroundColor Gray
            }
        } catch {
            Write-Host "   -> Erreur lors de l'arret du processus parent $parentPid : ${_}" -ForegroundColor Red
        }
    }
    Start-Sleep -Seconds 2
    Write-Host ""
}

# Étape 3: Vérifier que le port 5000 est libre
Write-Host "[3/4] Verification du port 5000..." -ForegroundColor Yellow
try {
    $port5000 = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
    if ($port5000) {
        Write-Host "   ATTENTION: Le port 5000 est toujours utilise!" -ForegroundColor Red
        $pidsOnPort = $port5000.OwningProcess | Select-Object -Unique
        Write-Host "   PID(s) utilisant le port: $($pidsOnPort -join ', ')" -ForegroundColor Red
        Write-Host "   Tentative d'arret du/des processus..." -ForegroundColor Yellow
        
        foreach ($pid in $pidsOnPort) {
            try {
                # Vérifier si le processus existe encore
                $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "   Arret du processus PID $pid..." -ForegroundColor White
                    Stop-Process -Id $pid -Force -ErrorAction Stop
                    Write-Host "   -> Processus $pid arrete" -ForegroundColor Green
                } else {
                    Write-Host "   -> Processus $pid deja arrete" -ForegroundColor Gray
                }
            } catch {
                Write-Host "   -> Erreur lors de l'arret du processus $pid : ${_}" -ForegroundColor Red
                # Essayer avec taskkill en dernier recours
                try {
                    taskkill /F /PID $pid | Out-Null
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "   -> Processus $pid arrete avec taskkill" -ForegroundColor Green
                    }
                } catch {
                    Write-Host "   -> Impossible d'arreter le processus $pid" -ForegroundColor Red
                }
            }
        }
        Start-Sleep -Seconds 2
        
        # Vérifier à nouveau
        $port5000After = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
        if ($port5000After) {
            Write-Host "   Le port 5000 est toujours utilise apres les tentatives" -ForegroundColor Yellow
        } else {
            Write-Host "   Le port 5000 est maintenant libre" -ForegroundColor Green
        }
    } else {
        Write-Host "   Le port 5000 est libre" -ForegroundColor Green
    }
} catch {
    Write-Host "   Le port 5000 est libre (aucune connexion trouvee)" -ForegroundColor Green
}

Write-Host ""

# Étape 4: Vérification finale et nettoyage supplémentaire si nécessaire
Write-Host "[4/4] Verification finale..." -ForegroundColor Yellow
$remainingProcesses = Get-Process python -ErrorAction SilentlyContinue
if ($remainingProcesses) {
    Write-Host "   ATTENTION: Il reste $($remainingProcesses.Count) processus Python!" -ForegroundColor Red
    foreach ($proc in $remainingProcesses) {
        Write-Host "   - PID $($proc.Id)" -ForegroundColor Red
        try {
            Write-Host "     -> Tentative d'arret force..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "     -> Processus $($proc.Id) arrete" -ForegroundColor Green
        } catch {
            Write-Host "     -> Erreur: ${_}" -ForegroundColor Red
        }
    }
    Start-Sleep -Seconds 2
    $remainingProcesses = Get-Process python -ErrorAction SilentlyContinue
    if ($remainingProcesses) {
        Write-Host "   ATTENTION: Certains processus resistent encore!" -ForegroundColor Red
        Write-Host "   PIDs restants: $($remainingProcesses.Id -join ', ')" -ForegroundColor Red
    } else {
        Write-Host "   SUCCES: Tous les processus Python ont ete arretes!" -ForegroundColor Green
    }
} else {
    Write-Host "   Aucun processus Python restant" -ForegroundColor Green
}

$port5000Final = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($port5000Final) {
    Write-Host "   ATTENTION: Le port 5000 est toujours utilise!" -ForegroundColor Red
    $pidsOnPort = $port5000Final.OwningProcess | Select-Object -Unique
    Write-Host "   PID(s) utilisant le port: $($pidsOnPort -join ', ')" -ForegroundColor Red
    foreach ($pid in $pidsOnPort) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Write-Host "   -> Processus $pid arrete" -ForegroundColor Green
        } catch {
            Write-Host "   -> Erreur lors de l'arret du processus $pid" -ForegroundColor Red
        }
    }
    Start-Sleep -Seconds 2
    $port5000Final = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
    if ($port5000Final) {
        Write-Host "   Le port 5000 est toujours utilise apres les tentatives" -ForegroundColor Yellow
    } else {
        Write-Host "   Le port 5000 est maintenant libre" -ForegroundColor Green
    }
} else {
    Write-Host "   Le port 5000 est libre" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if (-not $remainingProcesses -and -not $port5000Final) {
    Write-Host "SUCCES: Toutes les instances Flask ont ete arretees!" -ForegroundColor Green
} else {
    Write-Host "ATTENTION: Certaines instances peuvent encore etre actives" -ForegroundColor Yellow
    if ($remainingProcesses) {
        Write-Host ""
        Write-Host "Si les processus continuent de se recreer, cela peut indiquer:" -ForegroundColor Yellow
        Write-Host "- Un service Windows qui les recree automatiquement" -ForegroundColor White
        Write-Host "- Une tache planifiee qui relance Flask" -ForegroundColor White
        Write-Host "- Un processus de surveillance/watchdog" -ForegroundColor White
        Write-Host ""
        Write-Host "Pour identifier la source, executez:" -ForegroundColor Cyan
        Write-Host '  Get-Process | Where-Object {$_.Id -in @(' + ($remainingProcesses.Id -join ',') + ')} | Select-Object Id, ProcessName, Path' -ForegroundColor White
    }
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
