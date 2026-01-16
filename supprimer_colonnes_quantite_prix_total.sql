-- Script de suppression des colonnes QteComm_COMMANDES et PrixVenteTotal
-- de la table WEB_S_DOS_ENCOURS
-- Projet 19 - Gestion des Dossiers en Cours

USE novaprint_restored;
GO

-- Vérifier si la colonne QteComm_COMMANDES existe avant de la supprimer
IF EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
    AND COLUMN_NAME = 'QteComm_COMMANDES'
)
BEGIN
    ALTER TABLE WEB_S_DOS_ENCOURS
    DROP COLUMN QteComm_COMMANDES;
    
    PRINT 'Colonne QteComm_COMMANDES supprimée avec succès de WEB_S_DOS_ENCOURS';
END
ELSE
BEGIN
    PRINT 'La colonne QteComm_COMMANDES n''existe pas dans WEB_S_DOS_ENCOURS';
END
GO

-- Vérifier si la colonne PrixVenteTotal existe avant de la supprimer
IF EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
    AND COLUMN_NAME = 'PrixVenteTotal'
)
BEGIN
    ALTER TABLE WEB_S_DOS_ENCOURS
    DROP COLUMN PrixVenteTotal;
    
    PRINT 'Colonne PrixVenteTotal supprimée avec succès de WEB_S_DOS_ENCOURS';
END
ELSE
BEGIN
    PRINT 'La colonne PrixVenteTotal n''existe pas dans WEB_S_DOS_ENCOURS';
END
GO

-- Afficher la structure de la table après suppression
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    NUMERIC_PRECISION,
    NUMERIC_SCALE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS'
ORDER BY ORDINAL_POSITION;
GO

PRINT '';
PRINT '============================================================================';
PRINT 'SUPPRESSION TERMINEE';
PRINT 'Les colonnes QteComm_COMMANDES et PrixVenteTotal ont été supprimées';
PRINT '============================================================================';
GO
