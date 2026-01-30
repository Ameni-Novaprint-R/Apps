-- Verification des contraintes de WEB_DROITS_ACCES
USE novaprint_restored;
GO

PRINT 'Verification des contraintes de WEB_DROITS_ACCES';
PRINT '';

-- 1. Clé primaire
PRINT '1. Clé primaire:';
IF EXISTS (
    SELECT * FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES') AND type = 'PK'
)
BEGIN
    SELECT name AS Nom_PK FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES') AND type = 'PK';
    PRINT '  OK - Clé primaire existe';
END
ELSE
    PRINT '  ERREUR - Clé primaire manquante';
PRINT '';

-- 2. Contrainte UNIQUE (ID_Section, Action)
PRINT '2. Contrainte UNIQUE (ID_Section, Action):';
IF EXISTS (
    SELECT * FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
    AND name = 'UQ_WEB_DROITS_ACCES_ID_Section_Action'
)
    PRINT '  OK - Contrainte UNIQUE existe';
ELSE
    PRINT '  ERREUR - Contrainte UNIQUE manquante';
PRINT '';

-- 3. Clé étrangère vers WEB_SECTIONS
PRINT '3. Clé étrangère vers WEB_SECTIONS:';
IF EXISTS (
    SELECT * FROM sys.foreign_keys 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
    AND name = 'FK_WEB_DROITS_ACCES_ID_Section'
)
BEGIN
    SELECT 
        fk.name AS FK_Name,
        fk.delete_referential_action_desc AS Action_DELETE
    FROM sys.foreign_keys fk
    WHERE fk.parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
    AND fk.name = 'FK_WEB_DROITS_ACCES_ID_Section';
    PRINT '  OK - Clé étrangère existe';
END
ELSE
    PRINT '  ERREUR - Clé étrangère manquante';
PRINT '';

-- 4. Nombre de lignes
PRINT '4. Nombre de lignes:';
SELECT COUNT(*) AS Total FROM WEB_DROITS_ACCES;
PRINT '';

GO
