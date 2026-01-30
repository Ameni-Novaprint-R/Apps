-- Ajouter les contraintes manquantes à WEB_DROITS_ACCES
USE novaprint_restored;
GO

PRINT 'Ajout des contraintes manquantes à WEB_DROITS_ACCES';
PRINT '';

-- 1. Ajouter la clé primaire si elle manque
IF NOT EXISTS (
    SELECT * FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES') AND type = 'PK'
)
BEGIN
    ALTER TABLE dbo.WEB_DROITS_ACCES
    ADD CONSTRAINT PK_WEB_DROITS_ACCES PRIMARY KEY (ID);
    PRINT 'OK - Clé primaire PK_WEB_DROITS_ACCES ajoutée';
END
ELSE
    PRINT 'INFO - Clé primaire existe déjà';
PRINT '';

-- 2. Ajouter la contrainte UNIQUE si elle manque
IF NOT EXISTS (
    SELECT * FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
    AND name = 'UQ_WEB_DROITS_ACCES_ID_Section_Action'
)
BEGIN
    ALTER TABLE dbo.WEB_DROITS_ACCES
    ADD CONSTRAINT UQ_WEB_DROITS_ACCES_ID_Section_Action UNIQUE (ID_Section, Action);
    PRINT 'OK - Contrainte UNIQUE (ID_Section, Action) ajoutée';
END
ELSE
    PRINT 'INFO - Contrainte UNIQUE existe déjà';
PRINT '';

-- 3. Ajouter la clé étrangère si elle manque
IF NOT EXISTS (
    SELECT * FROM sys.foreign_keys 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
    AND name = 'FK_WEB_DROITS_ACCES_ID_Section'
)
BEGIN
    ALTER TABLE dbo.WEB_DROITS_ACCES
    ADD CONSTRAINT FK_WEB_DROITS_ACCES_ID_Section
    FOREIGN KEY (ID_Section) REFERENCES dbo.WEB_SECTIONS(ID) ON DELETE CASCADE;
    PRINT 'OK - Clé étrangère FK_WEB_DROITS_ACCES_ID_Section ajoutée';
END
ELSE
    PRINT 'INFO - Clé étrangère existe déjà';
PRINT '';

PRINT 'Terminé';
GO
