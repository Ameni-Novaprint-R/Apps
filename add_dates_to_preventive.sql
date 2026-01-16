/*
================================================================================
AJOUT DES COLONNES DE DATES À LA TABLE WEB_GMAO_PREVENTIVE
================================================================================
Ajoute DtePrev (date prévue) et DteReal (date de réalisation)
*/

USE novaprint_restored;
GO

-- Vérifier si les colonnes existent déjà
IF COL_LENGTH('dbo.WEB_GMAO_PREVENTIVE', 'DtePrev') IS NULL
BEGIN
    PRINT '📝 Ajout des colonnes de dates...'
    
    -- Date prévue de la maintenance préventive
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    ADD DtePrev DATETIME NULL;
    
    PRINT '✅ Colonne DtePrev ajoutée'
END
ELSE
BEGIN
    PRINT '⚠️ La colonne DtePrev existe déjà.'
END
GO

IF COL_LENGTH('dbo.WEB_GMAO_PREVENTIVE', 'DteReal') IS NULL
BEGIN
    -- Date de réalisation effective de la maintenance préventive
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    ADD DteReal DATETIME NULL;
    
    PRINT '✅ Colonne DteReal ajoutée'
END
ELSE
BEGIN
    PRINT '⚠️ La colonne DteReal existe déjà.'
END
GO

-- Créer des index pour améliorer les performances des recherches par date
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_WEB_GMAO_PREVENTIVE_DtePrev')
BEGIN
    CREATE NONCLUSTERED INDEX IX_WEB_GMAO_PREVENTIVE_DtePrev 
    ON dbo.WEB_GMAO_PREVENTIVE(DtePrev);
    PRINT '✅ Index sur DtePrev créé'
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_WEB_GMAO_PREVENTIVE_DteReal')
BEGIN
    CREATE NONCLUSTERED INDEX IX_WEB_GMAO_PREVENTIVE_DteReal 
    ON dbo.WEB_GMAO_PREVENTIVE(DteReal);
    PRINT '✅ Index sur DteReal créé'
END
GO

PRINT ''
PRINT '✅ Extension de la table WEB_GMAO_PREVENTIVE terminée!'
PRINT ''
PRINT '📌 Nouvelles colonnes ajoutées:'
PRINT '   - DtePrev : Date prévue de la maintenance préventive'
PRINT '   - DteReal : Date de réalisation effective de la maintenance préventive'
GO

















