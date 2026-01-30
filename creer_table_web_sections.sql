/*
================================================================================
CRÉATION DE LA TABLE WEB_SECTIONS
================================================================================
Base de données : novaprint_restored
Objectif : Définir les sections fonctionnelles de chaque projet, en vue de la
           gestion des accès par utilisateur (étape ultérieure).

Colonnes :
- ID      : clé primaire technique, auto-incrémentée
- ID_Proj : clé étrangère vers WEB_PROJETS(ID). Une section appartient à un
            seul projet.
- Nom     : nom de la section affiché à l'utilisateur
- archive : 0 par défaut (actif), 1 si la section est désactivée

Une section appartient obligatoirement à un seul projet.
UNIQUE (ID_Proj, Nom) : évite deux sections de même nom dans un même projet.
================================================================================
*/

USE [novaprint_restored]
GO

PRINT 'Création de la table WEB_SECTIONS...'
PRINT ''

-- ============================================================================
-- Créer la table si elle n'existe pas
-- ============================================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_SECTIONS')
BEGIN
    CREATE TABLE dbo.WEB_SECTIONS (
        ID      INT IDENTITY(1,1) NOT NULL,
        ID_Proj INT NOT NULL,
        Nom     NVARCHAR(200) NOT NULL,
        archive TINYINT NOT NULL DEFAULT 0,
        CONSTRAINT PK_WEB_SECTIONS PRIMARY KEY (ID),
        CONSTRAINT FK_WEB_SECTIONS_ID_Proj FOREIGN KEY (ID_Proj) REFERENCES dbo.WEB_PROJETS(ID) ON DELETE NO ACTION,
        CONSTRAINT UQ_WEB_SECTIONS_ID_Proj_Nom UNIQUE (ID_Proj, Nom)
    );

    PRINT 'Table WEB_SECTIONS créée.'
END
ELSE
BEGIN
    PRINT 'La table WEB_SECTIONS existe déjà.'
    -- Ajouter la FK si elle manque (table créée avant cette évolution)
    IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_WEB_SECTIONS_ID_Proj')
    BEGIN
        ALTER TABLE dbo.WEB_SECTIONS ADD CONSTRAINT FK_WEB_SECTIONS_ID_Proj
            FOREIGN KEY (ID_Proj) REFERENCES dbo.WEB_PROJETS(ID) ON DELETE NO ACTION;
        PRINT 'Contrainte FK_WEB_SECTIONS_ID_Proj ajoutée.'
    END
END
GO

-- ============================================================================
-- Résumé
-- ============================================================================
PRINT ''
PRINT 'Structure de la table WEB_SECTIONS :'
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    CASE WHEN COLUMNPROPERTY(OBJECT_ID('dbo.WEB_SECTIONS'), COLUMN_NAME, 'IsIdentity') = 1 THEN 'OUI' ELSE 'NON' END AS IS_IDENTITY
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'WEB_SECTIONS'
ORDER BY ORDINAL_POSITION;

PRINT ''
PRINT 'Contraintes :'
SELECT name, type_desc
FROM sys.objects
WHERE parent_object_id = OBJECT_ID('dbo.WEB_SECTIONS')
  AND type IN ('PK', 'F', 'UQ');

PRINT ''
SELECT COUNT(*) AS NbSections FROM dbo.WEB_SECTIONS;
PRINT 'Fin du script.'
GO
