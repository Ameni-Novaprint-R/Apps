-- ================================================================================
-- RENOMMAGE DE LA TABLE WEB_DROITS_ACCES EN WEB_ACTIONS
-- Base de données: novaprint_restored
-- Date: 29 Janvier 2026
-- ================================================================================
-- 
-- Ce script renomme la table WEB_DROITS_ACCES en WEB_ACTIONS ainsi que toutes
-- ses contraintes (clé primaire, clé étrangère, contrainte UNIQUE).
-- La structure de la table reste inchangée.
--
-- IMPORTANT: Exécuter ce script avec précaution et vérifier les dépendances
-- avant de l'exécuter en production.
-- ================================================================================

USE novaprint_restored;
GO

PRINT '================================================================================';
PRINT 'RENOMMAGE DE WEB_DROITS_ACCES EN WEB_ACTIONS';
PRINT '================================================================================';
PRINT '';

-- Vérifier que la table existe
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_DROITS_ACCES')
BEGIN
    PRINT 'ERREUR: La table WEB_DROITS_ACCES n''existe pas.';
    PRINT 'Arrêt du script.';
    RETURN;
END
PRINT '[OK] Table WEB_DROITS_ACCES trouvée.';
PRINT '';

-- Vérifier que la nouvelle table n'existe pas déjà
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_ACTIONS')
BEGIN
    PRINT 'ERREUR: La table WEB_ACTIONS existe déjà.';
    PRINT 'Arrêt du script pour éviter les conflits.';
    RETURN;
END
PRINT '[OK] La table WEB_ACTIONS n''existe pas encore.';
PRINT '';

-- ================================================================================
-- ÉTAPE 1: Renommer les contraintes
-- ================================================================================
PRINT '[1/3] Renommage des contraintes...';
PRINT '';

-- Renommer la clé primaire
IF EXISTS (
    SELECT * FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES') AND type = 'PK'
    AND name = 'PK_WEB_DROITS_ACCES'
)
BEGIN
    EXEC sp_rename 'PK_WEB_DROITS_ACCES', 'PK_WEB_ACTIONS', 'OBJECT';
    PRINT '  ✓ Clé primaire renommée: PK_WEB_DROITS_ACCES → PK_WEB_ACTIONS';
END
ELSE
    PRINT '  ⚠ Clé primaire PK_WEB_DROITS_ACCES non trouvée';

-- Renommer la contrainte UNIQUE
IF EXISTS (
    SELECT * FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
    AND name = 'UQ_WEB_DROITS_ACCES_ID_Section_Action'
)
BEGIN
    EXEC sp_rename 'UQ_WEB_DROITS_ACCES_ID_Section_Action', 'UQ_WEB_ACTIONS_ID_Section_Action', 'OBJECT';
    PRINT '  ✓ Contrainte UNIQUE renommée: UQ_WEB_DROITS_ACCES_ID_Section_Action → UQ_WEB_ACTIONS_ID_Section_Action';
END
ELSE
    PRINT '  ⚠ Contrainte UNIQUE UQ_WEB_DROITS_ACCES_ID_Section_Action non trouvée';

-- Renommer la clé étrangère
IF EXISTS (
    SELECT * FROM sys.foreign_keys 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
    AND name = 'FK_WEB_DROITS_ACCES_ID_Section'
)
BEGIN
    EXEC sp_rename 'FK_WEB_DROITS_ACCES_ID_Section', 'FK_WEB_ACTIONS_ID_Section', 'OBJECT';
    PRINT '  ✓ Clé étrangère renommée: FK_WEB_DROITS_ACCES_ID_Section → FK_WEB_ACTIONS_ID_Section';
END
ELSE
    PRINT '  ⚠ Clé étrangère FK_WEB_DROITS_ACCES_ID_Section non trouvée';

PRINT '';

-- ================================================================================
-- ÉTAPE 2: Renommer la table
-- ================================================================================
PRINT '[2/3] Renommage de la table...';
EXEC sp_rename 'dbo.WEB_DROITS_ACCES', 'WEB_ACTIONS';
PRINT '  ✓ Table renommée: WEB_DROITS_ACCES → WEB_ACTIONS';
PRINT '';

-- ================================================================================
-- ÉTAPE 3: Vérification
-- ================================================================================
PRINT '[3/3] Vérification du renommage...';
PRINT '';

-- Vérifier que la nouvelle table existe
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_ACTIONS')
    PRINT '  ✓ Table WEB_ACTIONS créée avec succès';
ELSE
    PRINT '  ✗ ERREUR: Table WEB_ACTIONS non trouvée après renommage';

-- Vérifier que l'ancienne table n'existe plus
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_DROITS_ACCES')
    PRINT '  ✓ Ancienne table WEB_DROITS_ACCES supprimée';
ELSE
    PRINT '  ✗ ATTENTION: Ancienne table WEB_DROITS_ACCES existe encore';

-- Vérifier les contraintes
IF EXISTS (SELECT * FROM sys.key_constraints WHERE parent_object_id = OBJECT_ID('dbo.WEB_ACTIONS') AND type = 'PK' AND name = 'PK_WEB_ACTIONS')
    PRINT '  ✓ Clé primaire PK_WEB_ACTIONS vérifiée';
ELSE
    PRINT '  ✗ Clé primaire PK_WEB_ACTIONS non trouvée';

IF EXISTS (SELECT * FROM sys.key_constraints WHERE parent_object_id = OBJECT_ID('dbo.WEB_ACTIONS') AND name = 'UQ_WEB_ACTIONS_ID_Section_Action')
    PRINT '  ✓ Contrainte UNIQUE UQ_WEB_ACTIONS_ID_Section_Action vérifiée';
ELSE
    PRINT '  ✗ Contrainte UNIQUE UQ_WEB_ACTIONS_ID_Section_Action non trouvée';

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE parent_object_id = OBJECT_ID('dbo.WEB_ACTIONS') AND name = 'FK_WEB_ACTIONS_ID_Section')
    PRINT '  ✓ Clé étrangère FK_WEB_ACTIONS_ID_Section vérifiée';
ELSE
    PRINT '  ✗ Clé étrangère FK_WEB_ACTIONS_ID_Section non trouvée';

-- Afficher le nombre de lignes
DECLARE @row_count INT;
SELECT @row_count = COUNT(*) FROM dbo.WEB_ACTIONS;
PRINT '';
PRINT '  Nombre de lignes dans WEB_ACTIONS: ' + CAST(@row_count AS VARCHAR(10));

PRINT '';
PRINT '================================================================================';
PRINT 'RENOMMAGE TERMINE';
PRINT '================================================================================';
PRINT '';
PRINT 'IMPORTANT: N''oubliez pas de mettre à jour le code Python qui référence';
PRINT '           WEB_DROITS_ACCES pour utiliser WEB_ACTIONS à la place.';
PRINT '';

GO
