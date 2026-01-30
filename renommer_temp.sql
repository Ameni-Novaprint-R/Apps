-- ================================================================================
-- RENOMMAGE DE LA TABLE WEB_DROITS_ACCES EN WEB_ACTIONS
-- Base de donnÃ©es: nova-- PRINT_restored
-- Date: 29 Janvier 2026
-- ================================================================================
-- 
-- Ce script renomme la table WEB_DROITS_ACCES en WEB_ACTIONS ainsi que toutes
-- ses contraintes (clÃ© primaire, clÃ© Ã©trangÃ¨re, contrainte UNIQUE).
-- La structure de la table reste inchangÃ©e.
--
-- IMPORTANT: ExÃ©cuter ce script avec prÃ©caution et vÃ©rifier les dÃ©pendances
-- avant de l'exÃ©cuter en production.
-- ================================================================================

USE nova-- PRINT_restored;
GO

-- PRINT '================================================================================';
-- PRINT 'RENOMMAGE DE WEB_DROITS_ACCES EN WEB_ACTIONS';
-- PRINT '================================================================================';
-- PRINT '';

-- VÃ©rifier que la table existe
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_DROITS_ACCES')
BEGIN
    -- PRINT 'ERREUR: La table WEB_DROITS_ACCES n''existe pas.';
    -- PRINT 'ArrÃªt du script.';
    RETURN;
END
-- PRINT '[OK] Table WEB_DROITS_ACCES trouvÃ©e.';
-- PRINT '';

-- VÃ©rifier que la nouvelle table n'existe pas dÃ©jÃ 
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_ACTIONS')
BEGIN
    -- PRINT 'ERREUR: La table WEB_ACTIONS existe dÃ©jÃ .';
    -- PRINT 'ArrÃªt du script pour Ã©viter les conflits.';
    RETURN;
END
-- PRINT '[OK] La table WEB_ACTIONS n''existe pas encore.';
-- PRINT '';

-- ================================================================================
-- Ã‰TAPE 1: Renommer les contraintes
-- ================================================================================
-- PRINT '[1/3] Renommage des contraintes...';
-- PRINT '';

-- Renommer la clÃ© primaire
IF EXISTS (
    SELECT * FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES') AND type = 'PK'
    AND name = 'PK_WEB_DROITS_ACCES'
)
BEGIN
    EXEC sp_rename 'PK_WEB_DROITS_ACCES', 'PK_WEB_ACTIONS', 'OBJECT';
    -- PRINT '  âœ“ ClÃ© primaire renommÃ©e: PK_WEB_DROITS_ACCES â†’ PK_WEB_ACTIONS';
END
ELSE
    -- PRINT '  âš  ClÃ© primaire PK_WEB_DROITS_ACCES non trouvÃ©e';

-- Renommer la contrainte UNIQUE
IF EXISTS (
    SELECT * FROM sys.key_constraints 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
    AND name = 'UQ_WEB_DROITS_ACCES_ID_Section_Action'
)
BEGIN
    EXEC sp_rename 'UQ_WEB_DROITS_ACCES_ID_Section_Action', 'UQ_WEB_ACTIONS_ID_Section_Action', 'OBJECT';
    -- PRINT '  âœ“ Contrainte UNIQUE renommÃ©e: UQ_WEB_DROITS_ACCES_ID_Section_Action â†’ UQ_WEB_ACTIONS_ID_Section_Action';
END
ELSE
    -- PRINT '  âš  Contrainte UNIQUE UQ_WEB_DROITS_ACCES_ID_Section_Action non trouvÃ©e';

-- Renommer la clÃ© Ã©trangÃ¨re
IF EXISTS (
    SELECT * FROM sys.foreign_keys 
    WHERE parent_object_id = OBJECT_ID('dbo.WEB_DROITS_ACCES')
    AND name = 'FK_WEB_DROITS_ACCES_ID_Section'
)
BEGIN
    EXEC sp_rename 'FK_WEB_DROITS_ACCES_ID_Section', 'FK_WEB_ACTIONS_ID_Section', 'OBJECT';
    -- PRINT '  âœ“ ClÃ© Ã©trangÃ¨re renommÃ©e: FK_WEB_DROITS_ACCES_ID_Section â†’ FK_WEB_ACTIONS_ID_Section';
END
ELSE
    -- PRINT '  âš  ClÃ© Ã©trangÃ¨re FK_WEB_DROITS_ACCES_ID_Section non trouvÃ©e';

-- PRINT '';

-- ================================================================================
-- Ã‰TAPE 2: Renommer la table
-- ================================================================================
-- PRINT '[2/3] Renommage de la table...';
EXEC sp_rename 'dbo.WEB_DROITS_ACCES', 'WEB_ACTIONS';
-- PRINT '  âœ“ Table renommÃ©e: WEB_DROITS_ACCES â†’ WEB_ACTIONS';
-- PRINT '';

-- ================================================================================
-- Ã‰TAPE 3: VÃ©rification
-- ================================================================================
-- PRINT '[3/3] VÃ©rification du renommage...';
-- PRINT '';

-- VÃ©rifier que la nouvelle table existe
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_ACTIONS')
    -- PRINT '  âœ“ Table WEB_ACTIONS crÃ©Ã©e avec succÃ¨s';
ELSE
    -- PRINT '  âœ— ERREUR: Table WEB_ACTIONS non trouvÃ©e aprÃ¨s renommage';

-- VÃ©rifier que l'ancienne table n'existe plus
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_DROITS_ACCES')
    -- PRINT '  âœ“ Ancienne table WEB_DROITS_ACCES supprimÃ©e';
ELSE
    -- PRINT '  âœ— ATTENTION: Ancienne table WEB_DROITS_ACCES existe encore';

-- VÃ©rifier les contraintes
IF EXISTS (SELECT * FROM sys.key_constraints WHERE parent_object_id = OBJECT_ID('dbo.WEB_ACTIONS') AND type = 'PK' AND name = 'PK_WEB_ACTIONS')
    -- PRINT '  âœ“ ClÃ© primaire PK_WEB_ACTIONS vÃ©rifiÃ©e';
ELSE
    -- PRINT '  âœ— ClÃ© primaire PK_WEB_ACTIONS non trouvÃ©e';

IF EXISTS (SELECT * FROM sys.key_constraints WHERE parent_object_id = OBJECT_ID('dbo.WEB_ACTIONS') AND name = 'UQ_WEB_ACTIONS_ID_Section_Action')
    -- PRINT '  âœ“ Contrainte UNIQUE UQ_WEB_ACTIONS_ID_Section_Action vÃ©rifiÃ©e';
ELSE
    -- PRINT '  âœ— Contrainte UNIQUE UQ_WEB_ACTIONS_ID_Section_Action non trouvÃ©e';

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE parent_object_id = OBJECT_ID('dbo.WEB_ACTIONS') AND name = 'FK_WEB_ACTIONS_ID_Section')
    -- PRINT '  âœ“ ClÃ© Ã©trangÃ¨re FK_WEB_ACTIONS_ID_Section vÃ©rifiÃ©e';
ELSE
    -- PRINT '  âœ— ClÃ© Ã©trangÃ¨re FK_WEB_ACTIONS_ID_Section non trouvÃ©e';

-- Afficher le nombre de lignes
DECLARE @row_count INT;
SELECT @row_count = COUNT(*) FROM dbo.WEB_ACTIONS;
-- PRINT '';
-- PRINT '  Nombre de lignes dans WEB_ACTIONS: ' + CAST(@row_count AS VARCHAR(10));

-- PRINT '';
-- PRINT '================================================================================';
-- PRINT 'RENOMMAGE TERMINE';
-- PRINT '================================================================================';
-- PRINT '';
-- PRINT 'IMPORTANT: N''oubliez pas de mettre Ã  jour le code Python qui rÃ©fÃ©rence';
-- PRINT '           WEB_DROITS_ACCES pour utiliser WEB_ACTIONS Ã  la place.';
-- PRINT '';

GO
