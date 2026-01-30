-- ================================================================================
-- VERIFICATION DE LA STRUCTURE DE WEB_DROITS_ACCES
-- ================================================================================
USE novaprint_restored;
GO

PRINT '================================================================================';
PRINT 'VERIFICATION DE LA TABLE WEB_DROITS_ACCES';
PRINT '================================================================================';
PRINT '';

-- 1. Vérifier l'existence de la table
PRINT '[1] Verification de l''existence de la table...';
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_DROITS_ACCES')
    PRINT '  ✓ Table WEB_DROITS_ACCES existe';
ELSE
    PRINT '  ✗ Table WEB_DROITS_ACCES n''existe pas';
PRINT '';

-- 2. Structure des colonnes
PRINT '[2] Structure des colonnes:';
SELECT 
    COLUMN_NAME AS Colonne,
    DATA_TYPE AS Type,
    CASE 
        WHEN CHARACTER_MAXIMUM_LENGTH IS NOT NULL 
        THEN CAST(DATA_TYPE AS VARCHAR) + '(' + CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR) + ')'
        ELSE DATA_TYPE
    END AS Type_Complet,
    IS_NULLABLE AS Nullable,
    COLUMN_DEFAULT AS Valeur_Defaut
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'WEB_DROITS_ACCES'
ORDER BY ORDINAL_POSITION;
PRINT '';

-- 3. Vérifier la clé primaire
PRINT '[3] Verification de la clé primaire...';
IF EXISTS (
    SELECT * FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES') AND type = 'PK'
)
BEGIN
    SELECT name AS Nom_PK
    FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES') AND type = 'PK';
    PRINT '  ✓ Clé primaire existe';
END
ELSE
    PRINT '  ✗ Clé primaire manquante';
PRINT '';

-- 4. Vérifier la contrainte UNIQUE (ID_Section, Action)
PRINT '[4] Verification de la contrainte UNIQUE (ID_Section, Action)...';
IF EXISTS (
    SELECT * FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
    AND name = 'UQ_WEB_DROITS_ACCES_ID_Section_Action'
)
    PRINT '  ✓ Contrainte UNIQUE (ID_Section, Action) existe';
ELSE
    PRINT '  ✗ Contrainte UNIQUE (ID_Section, Action) manquante';
PRINT '';

-- 5. Vérifier la clé étrangère vers WEB_SECTIONS
PRINT '[5] Verification de la clé étrangère vers WEB_SECTIONS...';
IF EXISTS (
    SELECT * FROM sys.foreign_keys 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
    AND name = 'FK_WEB_DROITS_ACCES_ID_Section'
)
BEGIN
    SELECT 
        fk.name AS FK_Name,
        tp.name AS Table_Parent,
        cp.name AS Colonne_Parent,
        tr.name AS Table_Referencee,
        cr.name AS Colonne_Referencee,
        fk.delete_referential_action_desc AS Action_DELETE
    FROM sys.foreign_keys AS fk
    INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
    INNER JOIN sys.tables AS tp ON fkc.parent_object_id = tp.object_id
    INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id 
        AND fkc.parent_column_id = cp.column_id
    INNER JOIN sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
    INNER JOIN sys.columns AS cr ON fkc.referenced_object_id = cr.object_id 
        AND fkc.referenced_column_id = cr.column_id
    WHERE fk.parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES');
    PRINT '  ✓ Clé étrangère existe';
END
ELSE
    PRINT '  ✗ Clé étrangère vers WEB_SECTIONS manquante';
PRINT '';

-- 6. Compter les lignes
PRINT '[6] Nombre de lignes dans la table:';
SELECT COUNT(*) AS Total_Lignes FROM WEB_DROITS_ACCES;
PRINT '';

-- 7. Conclusion
PRINT '================================================================================';
PRINT 'CONCLUSION';
PRINT '================================================================================';
DECLARE @has_table BIT = CASE WHEN EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_DROITS_ACCES') THEN 1 ELSE 0 END;
DECLARE @has_pk BIT = CASE WHEN EXISTS (SELECT * FROM sys.key_constraints WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES') AND type = 'PK') THEN 1 ELSE 0 END;
DECLARE @has_unique BIT = CASE WHEN EXISTS (SELECT * FROM sys.key_constraints WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES') AND name = 'UQ_WEB_DROITS_ACCES_ID_Section_Action') THEN 1 ELSE 0 END;
DECLARE @has_fk BIT = CASE WHEN EXISTS (SELECT * FROM sys.foreign_keys WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES') AND name = 'FK_WEB_DROITS_ACCES_ID_Section') THEN 1 ELSE 0 END;

IF @has_table = 1 AND @has_pk = 1 AND @has_unique = 1 AND @has_fk = 1
    PRINT '✓ La table WEB_DROITS_ACCES est correctement créée avec toutes les contraintes !';
ELSE
BEGIN
    PRINT '⚠ La table existe mais certaines contraintes manquent:';
    IF @has_pk = 0 PRINT '  ✗ Clé primaire manquante';
    IF @has_unique = 0 PRINT '  ✗ Contrainte UNIQUE (ID_Section, Action) manquante';
    IF @has_fk = 0 PRINT '  ✗ Clé étrangère vers WEB_SECTIONS manquante';
END
PRINT '';

GO
