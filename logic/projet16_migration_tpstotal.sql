-- Migration: Renommer TpsReel en TpsTotal dans WEB_GMAO_REPARATION
-- Exécuter ce script sur la base SQL Server avant de déployer la nouvelle version
-- Si TpsReel est une colonne calculée, adapter selon le schéma actuel

-- Pour une colonne stockée classique :
EXEC sp_rename 'WEB_GMAO_REPARATION.TpsReel', 'TpsTotal', 'COLUMN';
GO
