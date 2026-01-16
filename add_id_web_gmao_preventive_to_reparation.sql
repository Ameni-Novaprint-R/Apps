/*
================================================================================
AJOUT DE LA COLONNE ID_WEB_GMAO_PREVENTIVE DANS WEB_GMAO_REPARATION
================================================================================
Objectif : Ajouter une colonne pour référencer l'intervention préventive
associée à une fiche de réparation
*/

USE novaprint_restored;
GO

-- Vérifier si la colonne existe déjà
IF COL_LENGTH('dbo.WEB_GMAO_REPARATION', 'ID_WEB_GMAO_PREVENTIVE') IS NOT NULL
BEGIN
    PRINT '⚠️ La colonne ID_WEB_GMAO_PREVENTIVE existe déjà.'
    RETURN
END
GO

-- Ajouter la colonne ID_WEB_GMAO_PREVENTIVE
PRINT '📝 Ajout de la colonne ID_WEB_GMAO_PREVENTIVE...'
ALTER TABLE dbo.WEB_GMAO_REPARATION
ADD ID_WEB_GMAO_PREVENTIVE INT NULL;
GO

-- Ajouter la contrainte de clé étrangère
PRINT '📝 Ajout de la contrainte de clé étrangère...'
ALTER TABLE dbo.WEB_GMAO_REPARATION
ADD CONSTRAINT FK_WEB_GMAO_REPARATION_WEB_GMAO_PREVENTIVE 
    FOREIGN KEY (ID_WEB_GMAO_PREVENTIVE) REFERENCES WEB_GMAO_PREVENTIVE(ID) ON DELETE SET NULL;
GO

-- Créer un index pour améliorer les performances
PRINT '📝 Création de l''index...'
CREATE NONCLUSTERED INDEX IX_WEB_GMAO_REPARATION_ID_WEB_GMAO_PREVENTIVE 
    ON dbo.WEB_GMAO_REPARATION(ID_WEB_GMAO_PREVENTIVE);
GO

PRINT '✅ Colonne ID_WEB_GMAO_PREVENTIVE ajoutée avec succès!'
PRINT ''
PRINT '📌 Structure ajoutée:'
PRINT '   - ID_WEB_GMAO_PREVENTIVE : INT NULL (FK vers WEB_GMAO_PREVENTIVE.ID)'
PRINT '   - Contrainte FK : ON DELETE SET NULL'
PRINT '   - Index créé pour améliorer les performances'
GO














