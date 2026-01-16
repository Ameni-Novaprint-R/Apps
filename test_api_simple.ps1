# Script de test simple pour vérifier l'API
# Utilisation: .\test_api_simple.ps1 2025050176

param(
    [Parameter(Mandatory=$true)]
    [string]$NumeroDossier
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test de l'API pour le dossier: $NumeroDossier" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    $url = "http://127.0.0.1:5000/projet19/api/postes/$NumeroDossier"
    Write-Host "URL: $url" -ForegroundColor Yellow
    Write-Host ""
    
    $response = Invoke-WebRequest -Uri $url -ErrorAction Stop
    $json = $response.Content | ConvertFrom-Json
    
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Nombre de services: $($json.postes.Count)" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Détails de chaque service:" -ForegroundColor Cyan
    Write-Host "=========================" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($service in $json.postes) {
        Write-Host "Service: $($service.nom)" -ForegroundColor White
        Write-Host "  - ID: $($service.id)" -ForegroundColor Gray
        Write-Host "  - Cout: $($service.cout)" -ForegroundColor $(if ($service.cout -gt 0) { "Green" } else { "Red" })
        Write-Host "  - ID Fiche Travail: $($service.id_fiche_travail)" -ForegroundColor Gray
        Write-Host "  - Nom Poste: $($service.nom_poste)" -ForegroundColor Gray
        Write-Host ""
    }
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "RÉSULTAT:" -ForegroundColor Cyan
    
    $servicesAvecCout = ($json.postes | Where-Object { $_.cout -gt 0 }).Count
    $servicesSansCout = ($json.postes | Where-Object { $_.cout -eq 0 -or $null -eq $_.cout }).Count
    
    Write-Host "Services avec cout > 0: $servicesAvecCout" -ForegroundColor $(if ($servicesAvecCout -gt 0) { "Green" } else { "Red" })
    Write-Host "Services avec cout = 0 ou NULL: $servicesSansCout" -ForegroundColor $(if ($servicesSansCout -eq 0) { "Green" } else { "Red" })
    
    if ($servicesAvecCout -eq 0) {
        Write-Host ""
        Write-Host "PROBLÈME DÉTECTÉ: Aucun service n'a de coût !" -ForegroundColor Red
        Write-Host "L'API ne retourne pas les valeurs 'cout' correctement." -ForegroundColor Red
    } else {
        Write-Host ""
        Write-Host "L'API retourne bien les coûts !" -ForegroundColor Green
        Write-Host "Le problème est probablement dans le frontend JavaScript." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host ""
    Write-Host "ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Assurez-vous que Flask est démarré sur http://127.0.0.1:5000" -ForegroundColor Yellow
}
