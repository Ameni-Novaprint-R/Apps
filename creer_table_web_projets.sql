/*
================================================================================
CRÉATION DE LA TABLE WEB_PROJETS
================================================================================
Base de données : novaprint_restored
Objectif : Gérer la liste des projets affichés sur la page d'accueil du portail
           et préparer la limitation des accès par utilisateur (liaison avec
           personel et tables à créer ultérieurement).

Colonnes :
- ID        : clé primaire technique, auto-incrémentée
- NumProj   : numéro métier du projet (1–22). Projet 13 = placeholder (archive=1). ID=NumProj.
- CodeProj  : code du projet, partie avant « – » (ex : Projet 1, Projet 11)
- Nom       : nom affiché à l'utilisateur, partie après « – » (ex : Planning, Gestion des Traitements)
- archive   : 0 par défaut (actif), 1 si le projet est désactivé

Contraintes UNIQUE sur NumProj et sur CodeProj : un projet ne peut exister qu'une seule fois.

Cette table est uniquement destinée à la gestion des projets et des accès,
sans lien direct avec les tables métier internes de chaque projet.
================================================================================
*/

USE [novaprint_restored]
GO

PRINT 'Création de la table WEB_PROJETS...'
PRINT ''

-- ============================================================================
-- Créer la table si elle n'existe pas
-- ============================================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_PROJETS')
BEGIN
    CREATE TABLE dbo.WEB_PROJETS (
        ID        INT IDENTITY(1,1) NOT NULL,
        NumProj   INT NOT NULL,
        CodeProj  NVARCHAR(50) NOT NULL,
        Nom       NVARCHAR(200) NOT NULL,
        archive   TINYINT NOT NULL DEFAULT 0,
        CONSTRAINT PK_WEB_PROJETS PRIMARY KEY (ID),
        CONSTRAINT UQ_WEB_PROJETS_NumProj  UNIQUE (NumProj),
        CONSTRAINT UQ_WEB_PROJETS_CodeProj UNIQUE (CodeProj)
    );

    PRINT 'Table WEB_PROJETS créée.'
END
ELSE
BEGIN
    PRINT 'La table WEB_PROJETS existe déjà. Vérification des contraintes UNIQUE...'
    -- Ajouter UQ sur NumProj si elle manque (table créée avant cette évolution)
    IF NOT EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'UQ_WEB_PROJETS_NumProj' AND parent_object_id = OBJECT_ID('dbo.WEB_PROJETS'))
    BEGIN
        ALTER TABLE dbo.WEB_PROJETS ADD CONSTRAINT UQ_WEB_PROJETS_NumProj UNIQUE (NumProj);
        PRINT 'Contrainte UQ_WEB_PROJETS_NumProj ajoutée.'
    END
END
GO

-- ============================================================================
-- Insérer les projets initiaux (page d'accueil) si la table est vide
-- ============================================================================
IF NOT EXISTS (SELECT 1 FROM dbo.WEB_PROJETS)
BEGIN
    PRINT 'Insertion des projets initiaux...'

    SET NOCOUNT ON;

    INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive) VALUES
        (1,  N'Projet 1',  N'Planning', 0),
        (2,  N'Projet 2',  N'Gestion de commandes', 0),
        (3,  N'Projet 3',  N'Suivi BAT / Prépresse', 0),
        (4,  N'Projet 4',  N'Rapport de visite client', 0),
        (5,  N'Projet 5',  N'Planing production', 0),
        (6,  N'Projet 6',  N'Programme de voyage', 0),
        (7,  N'Projet 7',  N'Importation Factures STEG', 0),
        (8,  N'Projet 8',  N'Stats Devis/Commandes', 0),
        (9,  N'Projet 9',  N'Suivi Performance Livraison', 0),
        (10, N'Projet 10', N'Contrôle Qualité', 0),
        (11, N'Projet 11', N'Gestion des Traitements', 0),
        (12, N'Projet 12', N'Registre NC & Réclamations Clients', 0),
        (13, N'Projet 13', N'À venir', 1),   /* placeholder, à traiter en étape suivante */
        (14, N'Projet 14', N'Registre de suivi des déchets', 0),
        (15, N'Projet 15', N'Corrélation Déchets/CA', 0),
        (16, N'Projet 16', N'GMAO (Gestion de la Maintenance)', 0),
        (17, N'Projet 17', N'Fusion de fichiers HTML', 0),
        (18, N'Projet 18', N'Agenda Semainier 2026', 0),
        (19, N'Projet 19', N'Gestion des Dossiers en Cours', 0),
        (20, N'Projet 20', N'Analyse des Dossiers', 0),
        (21, N'Projet 21', N'Mise à jour Base de Données', 0),
        (22, N'Projet 22', N'Gestion des Employés', 0);

    SET NOCOUNT OFF;

    PRINT 'Projets initiaux insérés (22 projets, Projet 13 = placeholder archive=1, ID=NumProj).'
END
ELSE
BEGIN
    -- Si 21 lignes sans NumProj=13 : TRUNCATE et ré-insertion des 22 pour aligner ID=NumProj
    IF (SELECT COUNT(*) FROM dbo.WEB_PROJETS) = 21 AND NOT EXISTS (SELECT 1 FROM dbo.WEB_PROJETS WHERE NumProj = 13)
    BEGIN
        PRINT '21 lignes sans Projet 13 : TRUNCATE et ré-insertion des 22 projets pour aligner ID=NumProj.';
        TRUNCATE TABLE dbo.WEB_PROJETS;

        INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive) VALUES
            (1,  N'Projet 1',  N'Planning', 0),
            (2,  N'Projet 2',  N'Gestion de commandes', 0),
            (3,  N'Projet 3',  N'Suivi BAT / Prépresse', 0),
            (4,  N'Projet 4',  N'Rapport de visite client', 0),
            (5,  N'Projet 5',  N'Planing production', 0),
            (6,  N'Projet 6',  N'Programme de voyage', 0),
            (7,  N'Projet 7',  N'Importation Factures STEG', 0),
            (8,  N'Projet 8',  N'Stats Devis/Commandes', 0),
            (9,  N'Projet 9',  N'Suivi Performance Livraison', 0),
            (10, N'Projet 10', N'Contrôle Qualité', 0),
            (11, N'Projet 11', N'Gestion des Traitements', 0),
            (12, N'Projet 12', N'Registre NC & Réclamations Clients', 0),
            (13, N'Projet 13', N'À venir', 1),
            (14, N'Projet 14', N'Registre de suivi des déchets', 0),
            (15, N'Projet 15', N'Corrélation Déchets/CA', 0),
            (16, N'Projet 16', N'GMAO (Gestion de la Maintenance)', 0),
            (17, N'Projet 17', N'Fusion de fichiers HTML', 0),
            (18, N'Projet 18', N'Agenda Semainier 2026', 0),
            (19, N'Projet 19', N'Gestion des Dossiers en Cours', 0),
            (20, N'Projet 20', N'Analyse des Dossiers', 0),
            (21, N'Projet 21', N'Mise à jour Base de Données', 0),
            (22, N'Projet 22', N'Gestion des Employés', 0);

        PRINT '22 projets réinsérés. ID=NumProj (Projet 13 = placeholder archive=1).';
    END
    ELSE
    BEGIN
        PRINT 'La table WEB_PROJETS contient déjà des données. Mise à jour CodeProj et Nom.';
        UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 1',  Nom = N'Planning' WHERE NumProj = 1;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 2',  Nom = N'Gestion de commandes' WHERE NumProj = 2;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 3',  Nom = N'Suivi BAT / Prépresse' WHERE NumProj = 3;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 4',  Nom = N'Rapport de visite client' WHERE NumProj = 4;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 5',  Nom = N'Planing production' WHERE NumProj = 5;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 6',  Nom = N'Programme de voyage' WHERE NumProj = 6;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 7',  Nom = N'Importation Factures STEG' WHERE NumProj = 7;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 8',  Nom = N'Stats Devis/Commandes' WHERE NumProj = 8;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 9',  Nom = N'Suivi Performance Livraison' WHERE NumProj = 9;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 10', Nom = N'Contrôle Qualité' WHERE NumProj = 10;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 11', Nom = N'Gestion des Traitements' WHERE NumProj = 11;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 12', Nom = N'Registre NC & Réclamations Clients' WHERE NumProj = 12;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 13', Nom = N'À venir' WHERE NumProj = 13;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 14', Nom = N'Registre de suivi des déchets' WHERE NumProj = 14;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 15', Nom = N'Corrélation Déchets/CA' WHERE NumProj = 15;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 16', Nom = N'GMAO (Gestion de la Maintenance)' WHERE NumProj = 16;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 17', Nom = N'Fusion de fichiers HTML' WHERE NumProj = 17;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 18', Nom = N'Agenda Semainier 2026' WHERE NumProj = 18;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 19', Nom = N'Gestion des Dossiers en Cours' WHERE NumProj = 19;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 20', Nom = N'Analyse des Dossiers' WHERE NumProj = 20;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 21', Nom = N'Mise à jour Base de Données' WHERE NumProj = 21;
    UPDATE dbo.WEB_PROJETS SET CodeProj = N'Projet 22', Nom = N'Gestion des Employés' WHERE NumProj = 22;
    PRINT 'CodeProj et Nom mis à jour (convention : avant « – » = CodeProj, après = Nom).';
    END
END
GO

-- ============================================================================
-- Résumé
-- ============================================================================
PRINT ''
PRINT 'Structure de la table WEB_PROJETS :'
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    CASE WHEN COLUMNPROPERTY(OBJECT_ID('dbo.WEB_PROJETS'), COLUMN_NAME, 'IsIdentity') = 1 THEN 'OUI' ELSE 'NON' END AS IS_IDENTITY
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'WEB_PROJETS'
ORDER BY ORDINAL_POSITION;

PRINT ''
PRINT 'Contraintes :'
SELECT name, type_desc
FROM sys.objects
WHERE parent_object_id = OBJECT_ID('dbo.WEB_PROJETS')
  AND type IN ('PK', 'UQ');

PRINT ''
SELECT COUNT(*) AS NbProjets FROM dbo.WEB_PROJETS;
PRINT 'Fin du script.'
GO
