#!/usr/bin/env powershell
# -*- coding: utf-8 -*-
# Wrapper PowerShell pour exécuter le script d'arrêt Flask avec élévation automatique

# Vérifier si le script est exécuté en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "ELEVATION DES DROITS REQUISE" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ce script doit etre execute en tant qu'administrateur." -ForegroundColor White
    Write-Host "Relancement avec droits administrateur..." -ForegroundColor Cyan
    Write-Host ""
    
    # Relancer le script avec les droits administrateur
    $scriptPath = Join-Path $PSScriptRoot "arreter_toutes_instances_flask_admin.ps1"
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`"" -Verb RunAs
    exit
}

# Si on est déjà admin, exécuter le script directement
$scriptPath = Join-Path $PSScriptRoot "arreter_toutes_instances_flask_admin.ps1"
& $scriptPath
