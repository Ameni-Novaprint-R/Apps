-- Script pour ajouter les colonnes QteComm_COMMANDES et PrixVenteTotal
-- à la table WEB_S_DOS_ENCOURS pour le projet 19

USE NOVAPRINT_restored;
GO

-- Vérifier si la colonne QteComm_COMMANDES existe déjà
IF NOT EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
    AND COLUMN_NAME = 'QteComm_COMMANDES'
)
BEGIN
    ALTER TABLE WEB_S_DOS_ENCOURS
    ADD QteComm_COMMANDES INT NULL;
    
    PRINT 'Colonne QteComm_COMMANDES ajoutée avec succès à WEB_S_DOS_ENCOURS';
END
ELSE
BEGIN
    PRINT 'La colonne QteComm_COMMANDES existe déjà dans WEB_S_DOS_ENCOURS';
END
GO

-- Vérifier si la colonne PrixVenteTotal existe déjà
IF NOT EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
    AND COLUMN_NAME = 'PrixVenteTotal'
)
BEGIN
    ALTER TABLE WEB_S_DOS_ENCOURS
    ADD PrixVenteTotal DECIMAL(18,3) NULL;
    
    PRINT 'Colonne PrixVenteTotal ajoutée avec succès à WEB_S_DOS_ENCOURS';
END
ELSE
BEGIN
    PRINT 'La colonne PrixVenteTotal existe déjà dans WEB_S_DOS_ENCOURS';
END
GO

-- Vérifier la structure finale de la table
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    NUMERIC_PRECISION,
    NUMERIC_SCALE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS'
    AND COLUMN_NAME IN ('QteComm_COMMANDES', 'PrixVenteTotal', 'PrixVenteUnitaire')
ORDER BY COLUMN_NAME;
GO

PRINT 'Les colonnes QteComm_COMMANDES et PrixVenteTotal ont été ajoutées';
