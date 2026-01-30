#!/usr/bin/env powershell
# -*- coding: utf-8 -*-
# Script pour désactiver le service NSSM qui gère Flask

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "ATTENTION: Droits administrateur requis!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Ce script doit etre execute en tant qu'administrateur." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Pour executer en tant qu'administrateur:" -ForegroundColor Cyan
    Write-Host "1. Clic droit sur PowerShell" -ForegroundColor White
    Write-Host "2. Selectionner 'Executer en tant qu'administrateur'" -ForegroundColor White
    Write-Host "3. Naviguer vers C:\Apps" -ForegroundColor White
    Write-Host "4. Executer: .\desactiver_service_nssm.ps1" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DESACTIVATION DU SERVICE NSSM" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Étape 1: Trouver tous les services NSSM
Write-Host "[1/3] Recherche des services NSSM..." -ForegroundColor Yellow
$nssmServices = Get-Service | Where-Object { $_.Name -like "*nssm*" -or $_.DisplayName -like "*nssm*" -or $_.PathName -like "*nssm*" }

if ($nssmServices) {
    Write-Host "   Trouve $($nssmServices.Count) service(s) NSSM:" -ForegroundColor White
    foreach ($service in $nssmServices) {
        Write-Host "   - $($service.Name) : $($service.DisplayName)" -ForegroundColor Gray
        Write-Host "     Statut: $($service.Status)" -ForegroundColor $(if ($service.Status -eq 'Running') { 'Red' } else { 'Green' })
    }
} else {
    Write-Host "   Aucun service NSSM trouve directement." -ForegroundColor Yellow
    Write-Host "   Recherche des services geres par NSSM..." -ForegroundColor Yellow
    
    # Chercher les services qui utilisent nssm.exe dans leur chemin
    $allServices = Get-WmiObject Win32_Service | Where-Object { $_.PathName -like "*nssm*" }
    if ($allServices) {
        Write-Host "   Trouve $($allServices.Count) service(s) gere(s) par NSSM:" -ForegroundColor White
        foreach ($service in $allServices) {
            Write-Host "   - $($service.Name) : $($service.DisplayName)" -ForegroundColor Gray
            Write-Host "     Statut: $($service.State)" -ForegroundColor $(if ($service.State -eq 'Running') { 'Red' } else { 'Green' })
        }
        $nssmServices = $allServices
    } else {
        Write-Host "   Aucun service gere par NSSM trouve." -ForegroundColor Green
    }
}

Write-Host ""

# Étape 2: Arrêter et désactiver les services
if ($nssmServices) {
    Write-Host "[2/3] Arret et desactivation des services..." -ForegroundColor Yellow
    
    foreach ($service in $nssmServices) {
        $serviceName = if ($service.Name) { $service.Name } else { $service.Name }
        
        try {
            # Obtenir le service Windows
            $winService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
            if (-not $winService) {
                # Essayer avec WMI
                $winService = Get-WmiObject Win32_Service -Filter "Name='$serviceName'" -ErrorAction SilentlyContinue
            }
            
            if ($winService) {
                Write-Host "   Service: $serviceName" -ForegroundColor White
                
                # Arrêter le service s'il est en cours d'exécution
                if ($winService.Status -eq 'Running' -or $winService.State -eq 'Running') {
                    Write-Host "     -> Arret du service..." -ForegroundColor Yellow
                    Stop-Service -Name $serviceName -Force -ErrorAction Stop
                    Write-Host "     -> Service arrete" -ForegroundColor Green
                    Start-Sleep -Seconds 2
                } else {
                    Write-Host "     -> Service deja arrete" -ForegroundColor Gray
                }
                
                # Désactiver le service
                Write-Host "     -> Desactivation du service..." -ForegroundColor Yellow
                Set-Service -Name $serviceName -StartupType Disabled -ErrorAction Stop
                Write-Host "     -> Service desactive (ne demarrera plus automatiquement)" -ForegroundColor Green
            } else {
                Write-Host "   Service $serviceName introuvable" -ForegroundColor Red
            }
        } catch {
            Write-Host "   -> Erreur lors du traitement du service $serviceName : ${_}" -ForegroundColor Red
        }
    }
} else {
    Write-Host "[2/3] Aucun service a traiter" -ForegroundColor Green
}

Write-Host ""

# Étape 3: Vérification finale
Write-Host "[3/3] Verification finale..." -ForegroundColor Yellow
$remainingServices = Get-Service | Where-Object { $_.Name -like "*nssm*" -or $_.DisplayName -like "*nssm*" } | Where-Object { $_.Status -eq 'Running' }

if ($remainingServices) {
    Write-Host "   ATTENTION: Il reste $($remainingServices.Count) service(s) NSSM en cours d'execution!" -ForegroundColor Red
    foreach ($service in $remainingServices) {
        Write-Host "   - $($service.Name) : $($service.DisplayName)" -ForegroundColor Red
    }
} else {
    Write-Host "   SUCCES: Tous les services NSSM sont arretes et desactives!" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Termine!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Les services NSSM sont maintenant desactives." -ForegroundColor Green
Write-Host "Ils ne se relanceront plus automatiquement au demarrage." -ForegroundColor Green
Write-Host ""
Write-Host "Pour reactiver un service plus tard, utilisez:" -ForegroundColor Yellow
Write-Host "  Set-Service -Name <nom_du_service> -StartupType Manual" -ForegroundColor White
Write-Host "  OU" -ForegroundColor White
Write-Host "  Set-Service -Name <nom_du_service> -StartupType Automatic" -ForegroundColor White
Write-Host ""
