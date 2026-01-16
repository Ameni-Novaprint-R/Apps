-- Ajout de la colonne PrixVenteUnitaire à la table WEB_S_DOS_ENCOURS
-- Projet 19 - Gestion des Dossiers en Cours
-- Calcul : PrxVteReel / QteComm depuis COMMANDES

-- Vérifier si la colonne existe déjà
IF NOT EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
    AND COLUMN_NAME = 'PrixVenteUnitaire'
)
BEGIN
    ALTER TABLE WEB_S_DOS_ENCOURS
    ADD PrixVenteUnitaire DECIMAL(18,3) NULL;
    
    PRINT 'Colonne PrixVenteUnitaire ajoutée avec succès à WEB_S_DOS_ENCOURS';
END
ELSE
BEGIN
    PRINT 'La colonne PrixVenteUnitaire existe déjà dans WEB_S_DOS_ENCOURS';
END
GO
