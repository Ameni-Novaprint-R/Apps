-- Script SQL pour ajouter la colonne CtRel (Coût Total Réel) à la table WEB_S_DOS_ENCOURS
-- Formule: CtRel = (CoutTotal / QteComm_COMMANDES) * Quantité_application

USE novaprint_restored;
GO

-- Vérifier si la colonne existe déjà
IF NOT EXISTS (
    SELECT * 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
    AND COLUMN_NAME = 'CtRel'
)
BEGIN
    -- Ajouter la colonne CtRel
    ALTER TABLE WEB_S_DOS_ENCOURS
    ADD CtRel DECIMAL(18, 3) NULL;
    
    PRINT 'Colonne CtRel ajoutée avec succès à WEB_S_DOS_ENCOURS';
END
ELSE
BEGIN
    PRINT 'La colonne CtRel existe déjà dans WEB_S_DOS_ENCOURS';
END
GO
