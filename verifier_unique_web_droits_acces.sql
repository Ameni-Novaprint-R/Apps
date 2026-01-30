-- Verification de la contrainte UNIQUE (ID_Section, Action)
USE novaprint_restored;
GO

PRINT 'Verification de la contrainte UNIQUE (ID_Section, Action)';
PRINT '';

-- Vérifier si la contrainte UNIQUE existe
IF EXISTS (
    SELECT * FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
    AND name = 'UQ_WEB_DROITS_ACCES_ID_Section_Action'
)
BEGIN
    SELECT name AS Nom_Contrainte_UNIQUE 
    FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
    AND name = 'UQ_WEB_DROITS_ACCES_ID_Section_Action';
    PRINT 'OK - Contrainte UNIQUE (ID_Section, Action) existe';
END
ELSE
BEGIN
    PRINT 'ERREUR - Contrainte UNIQUE (ID_Section, Action) manquante';
    PRINT '';
    PRINT 'Pour l''ajouter, exécutez:';
    PRINT 'ALTER TABLE dbo.WEB_DROITS_ACCES';
    PRINT 'ADD CONSTRAINT UQ_WEB_DROITS_ACCES_ID_Section_Action UNIQUE (ID_Section, Action);';
END
PRINT '';

-- Lister toutes les contraintes de la table
PRINT 'Toutes les contraintes de WEB_DROITS_ACCES:';
SELECT 
    kc.name AS Nom_Contrainte,
    kc.type_desc AS Type,
    CASE kc.type
        WHEN 'PK' THEN 'Clé primaire'
        WHEN 'UQ' THEN 'Contrainte UNIQUE'
        ELSE kc.type_desc
    END AS Description
FROM sys.key_constraints kc
WHERE kc.parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
ORDER BY kc.type, kc.name;

GO
