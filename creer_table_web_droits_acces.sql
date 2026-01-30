-- ============================================================================
-- Script SQL pour créer la table WEB_DROITS_ACCES
-- Base de données: novaprint_restored
-- Description: Gestion des droits d'accès des employés aux actions des sections des projets
-- ============================================================================

USE novaprint_restored;
GO

-- Vérifier si la table existe déjà
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_DROITS_ACCES')
BEGIN
    PRINT 'La table WEB_DROITS_ACCES existe déjà.';
    PRINT 'Pour la recréer, exécutez d''abord: DROP TABLE WEB_DROITS_ACCES;';
    RETURN;
END
GO

-- Créer la table WEB_DROITS_ACCES
CREATE TABLE WEB_DROITS_ACCES (
    ID INT IDENTITY(1,1) NOT NULL,
    Matricule INT NOT NULL,
    ID_Action INT NOT NULL,
    Autorise BIT NOT NULL DEFAULT 1,
    
    -- Contraintes de clé primaire
    CONSTRAINT PK_WEB_DROITS_ACCES PRIMARY KEY (ID),
    
    -- Contraintes de clé étrangère
    CONSTRAINT FK_WEB_DROITS_ACCES_Matricule 
        FOREIGN KEY (Matricule) 
        REFERENCES personel(Matricule)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    CONSTRAINT FK_WEB_DROITS_ACCES_ID_Action 
        FOREIGN KEY (ID_Action) 
        REFERENCES WEB_ACTIONS(ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    
    -- Contrainte d'unicité : un employé ne peut avoir qu'un seul droit par action
    CONSTRAINT UQ_WEB_DROITS_ACCES_Matricule_ID_Action 
        UNIQUE (Matricule, ID_Action)
);
GO

-- Créer des index pour améliorer les performances
CREATE INDEX IDX_WEB_DROITS_ACCES_Matricule 
    ON WEB_DROITS_ACCES(Matricule);
GO

CREATE INDEX IDX_WEB_DROITS_ACCES_ID_Action 
    ON WEB_DROITS_ACCES(ID_Action);
GO

CREATE INDEX IDX_WEB_DROITS_ACCES_Autorise 
    ON WEB_DROITS_ACCES(Autorise);
GO

-- Vérification de la création
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_DROITS_ACCES')
BEGIN
    PRINT '========================================';
    PRINT 'Table WEB_DROITS_ACCES créée avec succès!';
    PRINT '========================================';
    PRINT '';
    PRINT 'Structure de la table:';
    PRINT '  - ID: INT IDENTITY(1,1) PRIMARY KEY';
    PRINT '  - Matricule: INT NOT NULL (FK -> personel.Matricule)';
    PRINT '  - ID_Action: INT NOT NULL (FK -> WEB_ACTIONS.ID)';
    PRINT '  - Autorise: BIT NOT NULL DEFAULT 1';
    PRINT '';
    PRINT 'Contraintes:';
    PRINT '  - PK_WEB_DROITS_ACCES: Clé primaire sur ID';
    PRINT '  - FK_WEB_DROITS_ACCES_Matricule: Clé étrangère vers personel(Matricule)';
    PRINT '  - FK_WEB_DROITS_ACCES_ID_Action: Clé étrangère vers WEB_ACTIONS(ID)';
    PRINT '  - UQ_WEB_DROITS_ACCES_Matricule_ID_Action: Unicité (Matricule, ID_Action)';
    PRINT '';
    PRINT 'Index créés:';
    PRINT '  - IDX_WEB_DROITS_ACCES_Matricule';
    PRINT '  - IDX_WEB_DROITS_ACCES_ID_Action';
    PRINT '  - IDX_WEB_DROITS_ACCES_Autorise';
    PRINT '';
END
ELSE
BEGIN
    PRINT 'ERREUR: La table WEB_DROITS_ACCES n''a pas été créée.';
END
GO
