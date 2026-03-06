@echo off
REM =============================================================================
REM Nettoyage des verrous projet11 (WEB_TRAITEMENTS_OUVERTURE)
REM À planifier dans le Planificateur de tâches Windows à 23h59 chaque jour.
REM =============================================================================
REM Modifiez l'URL ci-dessous si votre application tourne ailleurs (serveur, port).
set BASE_URL=http://localhost:5000
REM =============================================================================

powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%BASE_URL%/projet11/api/nettoyage-verrous' -Method POST -UseBasicParsing -TimeoutSec 30; Write-Host 'OK:' $r.Content } catch { Write-Host 'Erreur:' $_.Exception.Message; exit 1 }"
