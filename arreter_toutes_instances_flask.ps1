#!/usr/bin/env powershell
# -*- coding: utf-8 -*-
# Script pour arrêter toutes les instances Flask en cours d'exécution

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ARRET DE TOUTES LES INSTANCES FLASK" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Étape 1: Trouver tous les processus Python
Write-Host "[1/4] Recherche des processus Python..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "   Trouve $($pythonProcesses.Count) processus Python" -ForegroundColor White
    
    # Afficher les détails de chaque processus
    foreach ($proc in $pythonProcesses) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            Write-Host "   - PID $($proc.Id): $($cmdLine)" -ForegroundColor Gray
            
            # Vérifier si c'est Flask (app.py, run_flask_with_watchdog.py, etc.)
            if ($cmdLine -match 'app\.py|run_flask|flask|watchdog') {
                Write-Host "     -> Instance Flask detectee!" -ForegroundColor Red
            }
        } catch {
            Write-Host "   - PID $($proc.Id): (impossible de lire la ligne de commande)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "   Aucun processus Python trouve" -ForegroundColor Green
}

Write-Host ""

# Étape 2: Arrêter tous les processus Python
Write-Host "[2/4] Arret de tous les processus Python..." -ForegroundColor Yellow
if ($pythonProcesses) {
    $stopped = 0
    $failed = 0
    foreach ($proc in $pythonProcesses) {
        try {
            Write-Host "   Arret du processus PID $($proc.Id)..." -ForegroundColor White
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "   -> Processus $($proc.Id) arrete" -ForegroundColor Green
            $stopped++
        } catch {
            Write-Host "   -> Erreur lors de l'arret du processus $($proc.Id): $_" -ForegroundColor Red
            Write-Host "      Essayez d'executer ce script en tant qu'administrateur" -ForegroundColor Yellow
            $failed++
        }
    }
    Start-Sleep -Seconds 2
    if ($stopped -gt 0) {
        Write-Host "   $stopped processus arrete(s)" -ForegroundColor Green
    }
    if ($failed -gt 0) {
        Write-Host "   $failed processus n'ont pas pu etre arretes (permissions insuffisantes)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   Aucun processus a arreter" -ForegroundColor Green
}

Write-Host ""

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
            $killed = $false
            # Essayer plusieurs méthodes
            try {
                Stop-Process -Id $pid -Force -ErrorAction Stop
                $killed = $true
            } catch {
                try {
                    taskkill /F /PID $pid | Out-Null
                    if ($LASTEXITCODE -eq 0) { $killed = $true }
                } catch {
                    Write-Host "   -> Impossible d'arreter le processus $pid" -ForegroundColor Red
                }
            }
            
            if ($killed) {
                Write-Host "   -> Processus $pid arrete" -ForegroundColor Green
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

# Étape 4: Vérification finale
Write-Host "[4/4] Verification finale..." -ForegroundColor Yellow
$remainingProcesses = Get-Process python -ErrorAction SilentlyContinue
if ($remainingProcesses) {
    Write-Host "   ATTENTION: Il reste $($remainingProcesses.Count) processus Python!" -ForegroundColor Red
    foreach ($proc in $remainingProcesses) {
        Write-Host "   - PID $($proc.Id)" -ForegroundColor Red
    }
} else {
    Write-Host "   Aucun processus Python restant" -ForegroundColor Green
}

$port5000Final = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($port5000Final) {
    Write-Host "   ATTENTION: Le port 5000 est toujours utilise!" -ForegroundColor Red
} else {
    Write-Host "   Le port 5000 est libre" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if (-not $remainingProcesses -and -not $port5000Final) {
    Write-Host "SUCCES: Toutes les instances Flask ont ete arretees!" -ForegroundColor Green
} else {
    Write-Host "ATTENTION: Certaines instances peuvent encore etre actives" -ForegroundColor Yellow
    Write-Host "Vous pouvez essayer de les arreter manuellement ou redemarrer votre ordinateur" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
