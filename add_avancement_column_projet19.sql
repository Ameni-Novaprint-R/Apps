-- Ajout de la colonne Avancement (Nom_GP_SERVICES) à la table WEB_S_DOS_ENCOURS
-- Projet 19 - Gestion des Dossiers en Cours
-- CORRECTION : Utilise Nom_GP_SERVICES au lieu de Nom_GP_POSTES

-- Vérifier si la colonne existe déjà
IF NOT EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
    AND COLUMN_NAME = 'Nom_GP_SERVICES'
)
BEGIN
    ALTER TABLE WEB_S_DOS_ENCOURS
    ADD Nom_GP_SERVICES NVARCHAR(255) NULL;
    
    PRINT 'Colonne Nom_GP_SERVICES ajoutée avec succès à WEB_S_DOS_ENCOURS';
END
ELSE
BEGIN
    PRINT 'La colonne Nom_GP_SERVICES existe déjà dans WEB_S_DOS_ENCOURS';
END
GO

-- Supprimer l'ancienne colonne Nom_GP_POSTES si elle existe (migration)
IF EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
    AND COLUMN_NAME = 'Nom_GP_POSTES'
)
BEGIN
    -- Copier les données si nécessaire avant suppression
    UPDATE WEB_S_DOS_ENCOURS
    SET Nom_GP_SERVICES = Nom_GP_POSTES
    WHERE Nom_GP_SERVICES IS NULL AND Nom_GP_POSTES IS NOT NULL;
    
    ALTER TABLE WEB_S_DOS_ENCOURS
    DROP COLUMN Nom_GP_POSTES;
    
    PRINT 'Ancienne colonne Nom_GP_POSTES supprimée (données migrées vers Nom_GP_SERVICES)';
END
GO
