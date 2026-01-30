-- ============================================================================
-- Script de création de la table WEB_DROITS_ACCES
-- Base de données: novaprint_restored
-- Serveur: 192.168.10.225
-- ============================================================================
-- Description: Table pour gérer les droits d'accès des employés aux actions 
--              des sections des projets de la page web
-- ============================================================================

USE novaprint_restored;
GO

-- Vérifier si la table existe déjà et la supprimer si nécessaire
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_DROITS_ACCES')
BEGIN
    PRINT 'Suppression de la table WEB_DROITS_ACCES existante...';
    DROP TABLE [dbo].[WEB_DROITS_ACCES];
    PRINT 'Table WEB_DROITS_ACCES supprimee.';
END
GO

-- Créer la table WEB_DROITS_ACCES
CREATE TABLE [dbo].[WEB_DROITS_ACCES] (
    [ID] INT IDENTITY(1,1) NOT NULL,
    [Matricule] INT NOT NULL,
    [ID_Action] INT NOT NULL,
    [Autorise] BIT NOT NULL DEFAULT 1,
    
    -- Contrainte de clé primaire
    CONSTRAINT [PK_WEB_DROITS_ACCES] PRIMARY KEY CLUSTERED ([ID] ASC),
    
    -- Contrainte de clé étrangère vers personel(Matricule)
    CONSTRAINT [FK_WEB_DROITS_ACCES_Matricule] FOREIGN KEY ([Matricule])
        REFERENCES [dbo].[personel] ([Matricule])
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    -- Contrainte de clé étrangère vers WEB_ACTIONS(ID)
    CONSTRAINT [FK_WEB_DROITS_ACCES_ID_Action] FOREIGN KEY ([ID_Action])
        REFERENCES [dbo].[WEB_ACTIONS] ([ID])
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    -- Contrainte unique pour éviter les doublons (un employé ne peut avoir qu'un seul droit par action)
    CONSTRAINT [UQ_WEB_DROITS_ACCES_Matricule_Action] UNIQUE ([Matricule], [ID_Action])
);
GO

-- Créer un index sur Matricule pour améliorer les performances des requêtes
CREATE NONCLUSTERED INDEX [IX_WEB_DROITS_ACCES_Matricule] 
ON [dbo].[WEB_DROITS_ACCES] ([Matricule] ASC);
GO

-- Créer un index sur ID_Action pour améliorer les performances des requêtes
CREATE NONCLUSTERED INDEX [IX_WEB_DROITS_ACCES_ID_Action] 
ON [dbo].[WEB_DROITS_ACCES] ([ID_Action] ASC);
GO

-- Créer un index composite sur Matricule et Autorise pour les recherches fréquentes
CREATE NONCLUSTERED INDEX [IX_WEB_DROITS_ACCES_Matricule_Autorise] 
ON [dbo].[WEB_DROITS_ACCES] ([Matricule] ASC, [Autorise] ASC);
GO

PRINT 'Table WEB_DROITS_ACCES creee avec succes!';
PRINT 'Colonnes:';
PRINT '  - ID: INT IDENTITY(1,1) PRIMARY KEY';
PRINT '  - Matricule: INT NOT NULL (FK vers personel.Matricule)';
PRINT '  - ID_Action: INT NOT NULL (FK vers WEB_ACTIONS.ID)';
PRINT '  - Autorise: BIT NOT NULL DEFAULT 1';
PRINT '';
PRINT 'Contraintes:';
PRINT '  - PK_WEB_DROITS_ACCES: Clé primaire sur ID';
PRINT '  - FK_WEB_DROITS_ACCES_Matricule: Clé étrangère vers personel(Matricule)';
PRINT '  - FK_WEB_DROITS_ACCES_ID_Action: Clé étrangère vers WEB_ACTIONS(ID)';
PRINT '  - UQ_WEB_DROITS_ACCES_Matricule_Action: Contrainte unique (Matricule, ID_Action)';
PRINT '';
PRINT 'Index crees:';
PRINT '  - IX_WEB_DROITS_ACCES_Matricule';
PRINT '  - IX_WEB_DROITS_ACCES_ID_Action';
PRINT '  - IX_WEB_DROITS_ACCES_Matricule_Autorise';
GO
