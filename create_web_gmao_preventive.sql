/*
================================================================================
CRÉATION DE LA TABLE WEB_GMAO_PREVENTIVE
================================================================================
Objectif : Créer une table pour gérer les interventions préventives
avec synchronisation automatique depuis GP_POSTES et personel
*/

USE novaprint_restored;
GO

-- Vérifier si la table existe déjà
IF OBJECT_ID('dbo.WEB_GMAO_PREVENTIVE', 'U') IS NOT NULL
BEGIN
    PRINT '⚠️ La table WEB_GMAO_PREVENTIVE existe déjà.'
    PRINT 'Pour recréer la table, supprimez-la d''abord avec: DROP TABLE WEB_GMAO_PREVENTIVE;'
    RETURN
END
GO

-- Créer la table WEB_GMAO_PREVENTIVE
PRINT '📝 Création de la table WEB_GMAO_PREVENTIVE...'
CREATE TABLE dbo.WEB_GMAO_PREVENTIVE (
    -- Clé primaire
    ID INT IDENTITY(1,1) PRIMARY KEY,
    
    -- Machine sur laquelle l'intervention préventive a été réalisée
    -- Doit être un choix issu de GP_POSTES.Nom (lecture seule depuis la page)
    Nom_GP_POSTES VARCHAR(50) NULL,
    
    -- Nom complet de l'opérateur (copie de Nom + Prenom de personel)
    NomPrenom_personel NVARCHAR(101) NULL,
    
    -- Matricule de l'opérateur (FK vers personel.Matricule)
    Matricule_personel INT NULL,
    
    -- Métadonnées
    DateCreation DATETIME DEFAULT GETDATE(),
    DateModification DATETIME DEFAULT GETDATE(),
    
    -- Contraintes
    CONSTRAINT FK_WEB_GMAO_PREVENTIVE_personel 
        FOREIGN KEY (Matricule_personel) REFERENCES personel(Matricule)
);
GO

-- Créer des index pour améliorer les performances
PRINT '📝 Création des index...'
CREATE NONCLUSTERED INDEX IX_WEB_GMAO_PREVENTIVE_Matricule_personel 
    ON dbo.WEB_GMAO_PREVENTIVE(Matricule_personel);
GO

CREATE NONCLUSTERED INDEX IX_WEB_GMAO_PREVENTIVE_Nom_GP_POSTES 
    ON dbo.WEB_GMAO_PREVENTIVE(Nom_GP_POSTES);
GO

-- ============================================================================
-- TRIGGERS POUR SYNCHRONISATION AUTOMATIQUE
-- ============================================================================

-- TRIGGER 1: Mise à jour automatique depuis GP_POSTES
-- Quand le nom d'un poste est modifié dans GP_POSTES, mettre à jour toutes les occurrences dans WEB_GMAO_PREVENTIVE
PRINT '📝 Création du trigger TR_GP_POSTES_UPDATE_WEB_GMAO_PREVENTIVE...'
IF OBJECT_ID('TR_GP_POSTES_UPDATE_WEB_GMAO_PREVENTIVE', 'TR') IS NOT NULL
    DROP TRIGGER TR_GP_POSTES_UPDATE_WEB_GMAO_PREVENTIVE
GO

CREATE TRIGGER TR_GP_POSTES_UPDATE_WEB_GMAO_PREVENTIVE
ON [dbo].[GP_POSTES]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Mettre à jour Nom_GP_POSTES dans WEB_GMAO_PREVENTIVE si le nom a changé
    UPDATE w
    SET w.Nom_GP_POSTES = i.Nom,
        w.DateModification = GETDATE()
    FROM [dbo].[WEB_GMAO_PREVENTIVE] w
    INNER JOIN inserted i ON w.Nom_GP_POSTES = (SELECT Nom FROM deleted WHERE ID = i.ID)
    WHERE i.Nom IS NOT NULL AND i.Nom != '';
END
GO

-- TRIGGER 2: Mise à jour automatique depuis personel
-- Quand le nom ou prénom d'un opérateur est modifié dans personel, mettre à jour NomPrenom_personel dans WEB_GMAO_PREVENTIVE
PRINT '📝 Création du trigger TR_PERSONEL_UPDATE_WEB_GMAO_PREVENTIVE...'
IF OBJECT_ID('TR_PERSONEL_UPDATE_WEB_GMAO_PREVENTIVE', 'TR') IS NOT NULL
    DROP TRIGGER TR_PERSONEL_UPDATE_WEB_GMAO_PREVENTIVE
GO

CREATE TRIGGER TR_PERSONEL_UPDATE_WEB_GMAO_PREVENTIVE
ON [dbo].[personel]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Mettre à jour NomPrenom_personel dans WEB_GMAO_PREVENTIVE si le nom ou prénom a changé
    UPDATE w
    SET w.NomPrenom_personel = LTRIM(RTRIM(COALESCE(i.Nom, '') + ' ' + COALESCE(i.Prenom, ''))),
        w.DateModification = GETDATE()
    FROM [dbo].[WEB_GMAO_PREVENTIVE] w
    INNER JOIN inserted i ON w.Matricule_personel = i.Matricule
    WHERE i.Matricule IS NOT NULL;
END
GO

-- TRIGGER 3: Insertion automatique de NomPrenom_personel lors de l'insertion dans WEB_GMAO_PREVENTIVE
-- Garantit que NomPrenom_personel est toujours synchronisé avec personel lors de l'insertion
PRINT '📝 Création du trigger TR_WEB_GMAO_PREVENTIVE_INSERT...'
IF OBJECT_ID('TR_WEB_GMAO_PREVENTIVE_INSERT', 'TR') IS NOT NULL
    DROP TRIGGER TR_WEB_GMAO_PREVENTIVE_INSERT
GO

CREATE TRIGGER TR_WEB_GMAO_PREVENTIVE_INSERT
ON [dbo].[WEB_GMAO_PREVENTIVE]
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Mettre à jour NomPrenom_personel depuis personel lors de l'insertion
    UPDATE w
    SET w.NomPrenom_personel = LTRIM(RTRIM(COALESCE(p.Nom, '') + ' ' + COALESCE(p.Prenom, '')))
    FROM [dbo].[WEB_GMAO_PREVENTIVE] w
    INNER JOIN inserted i ON w.ID = i.ID
    LEFT JOIN [dbo].[personel] p ON w.Matricule_personel = p.Matricule
    WHERE w.Matricule_personel IS NOT NULL;
END
GO

-- TRIGGER 4: Mise à jour automatique de NomPrenom_personel lors de la mise à jour dans WEB_GMAO_PREVENTIVE
-- Garantit que NomPrenom_personel est toujours synchronisé avec personel lors de la mise à jour
PRINT '📝 Création du trigger TR_WEB_GMAO_PREVENTIVE_UPDATE...'
IF OBJECT_ID('TR_WEB_GMAO_PREVENTIVE_UPDATE', 'TR') IS NOT NULL
    DROP TRIGGER TR_WEB_GMAO_PREVENTIVE_UPDATE
GO

CREATE TRIGGER TR_WEB_GMAO_PREVENTIVE_UPDATE
ON [dbo].[WEB_GMAO_PREVENTIVE]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Mettre à jour NomPrenom_personel depuis personel si Matricule_personel a changé
    UPDATE w
    SET w.NomPrenom_personel = LTRIM(RTRIM(COALESCE(p.Nom, '') + ' ' + COALESCE(p.Prenom, ''))),
        w.DateModification = GETDATE()
    FROM [dbo].[WEB_GMAO_PREVENTIVE] w
    INNER JOIN inserted i ON w.ID = i.ID
    LEFT JOIN [dbo].[personel] p ON w.Matricule_personel = p.Matricule
    WHERE w.Matricule_personel IS NOT NULL
      AND (i.Matricule_personel != (SELECT Matricule_personel FROM deleted WHERE ID = i.ID)
           OR i.Matricule_personel IS NOT NULL);
END
GO

PRINT ''
PRINT '✅ Table WEB_GMAO_PREVENTIVE créée avec succès!'
PRINT ''
PRINT '📌 Structure de la table:'
PRINT '   - ID : Identifiant unique (IDENTITY)'
PRINT '   - Nom_GP_POSTES : Nom de la machine (lecture seule depuis la page)'
PRINT '   - NomPrenom_personel : Nom complet de l''opérateur (synchronisé automatiquement)'
PRINT '   - Matricule_personel : Matricule de l''opérateur (FK vers personel.Matricule)'
PRINT '   - DateCreation : Date de création'
PRINT '   - DateModification : Date de modification'
PRINT ''
PRINT '🔄 Triggers créés:'
PRINT '   - TR_GP_POSTES_UPDATE_WEB_GMAO_PREVENTIVE : Synchronise Nom_GP_POSTES depuis GP_POSTES'
PRINT '   - TR_PERSONEL_UPDATE_WEB_GMAO_PREVENTIVE : Synchronise NomPrenom_personel depuis personel'
PRINT '   - TR_WEB_GMAO_PREVENTIVE_INSERT : Synchronise NomPrenom_personel lors de l''insertion'
PRINT '   - TR_WEB_GMAO_PREVENTIVE_UPDATE : Synchronise NomPrenom_personel lors de la mise à jour'
PRINT ''
PRINT '⚠️ IMPORTANT:'
PRINT '   - Les données de GP_POSTES et personel sont en lecture seule depuis la page'
PRINT '   - Toute mise à jour dans GP_POSTES ou personel sera automatiquement reflétée dans WEB_GMAO_PREVENTIVE'
GO

















