-- ================================================================================
-- CORRECTION DES IDs SPECIFIQUES DANS WEB_DROITS_ACCES
-- ================================================================================
-- Ce script met à jour les IDs existants au lieu d'insérer
-- ID 6 : EXPORT_EXCEL, ID_Section = 2 (Liste des Traitements)
-- ID 7 : EXPORT_PDF, ID_Section = 2 (Liste des Traitements)
-- ID 8 : CONSULTATION, ID_Section = 3 (Statistiques)
-- ================================================================================
USE novaprint_restored;
GO

PRINT 'Correction des IDs specifiques dans WEB_DROITS_ACCES';
PRINT '';

-- Vérifier l'état actuel
PRINT 'Etat actuel:';
SELECT ID, ID_Section, Action, archive 
FROM WEB_DROITS_ACCES 
WHERE ID IN (6, 7, 8) OR (ID_Section = 2 AND Action IN ('EXPORT_EXCEL', 'EXPORT_PDF')) OR (ID_Section = 3 AND Action = 'CONSULTATION')
ORDER BY ID;
PRINT '';

-- Correction ID 6: EXPORT_EXCEL, ID_Section=2
PRINT 'Correction ID 6: EXPORT_EXCEL, ID_Section=2';
DECLARE @id6_existing INT;
SELECT @id6_existing = ID FROM WEB_DROITS_ACCES WHERE ID_Section = 2 AND Action = 'EXPORT_EXCEL';

IF @id6_existing IS NOT NULL AND @id6_existing != 6
BEGIN
    -- Supprimer l'ID 6 s'il existe avec des valeurs incorrectes
    DELETE FROM WEB_DROITS_ACCES WHERE ID = 6 AND (ID_Section != 2 OR Action != 'EXPORT_EXCEL');
    -- Mettre à jour l'ID de l'enregistrement existant vers 6
    UPDATE WEB_DROITS_ACCES SET ID = 6, archive = 0 WHERE ID = @id6_existing;
    PRINT '  ✓ ID ' + CAST(@id6_existing AS VARCHAR) + ' modifié vers ID 6: ID_Section=2, Action=EXPORT_EXCEL';
END
ELSE IF @id6_existing = 6
BEGIN
    UPDATE WEB_DROITS_ACCES SET archive = 0 WHERE ID = 6;
    PRINT '  ✓ ID 6 déjà correct, archive = 0';
END
ELSE
BEGIN
    -- Vérifier si ID 6 existe avec des valeurs incorrectes
    IF EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID = 6)
    BEGIN
        UPDATE WEB_DROITS_ACCES SET ID_Section = 2, Action = 'EXPORT_EXCEL', archive = 0 WHERE ID = 6;
        PRINT '  ✓ ID 6 corrigé: ID_Section=2, Action=EXPORT_EXCEL';
    END
    ELSE
    BEGIN
        INSERT INTO WEB_DROITS_ACCES (ID, ID_Section, Action, archive) VALUES (6, 2, 'EXPORT_EXCEL', 0);
        PRINT '  + ID 6 créé: ID_Section=2, Action=EXPORT_EXCEL';
    END
END
PRINT '';

-- Correction ID 7: EXPORT_PDF, ID_Section=2
PRINT 'Correction ID 7: EXPORT_PDF, ID_Section=2';
DECLARE @id7_existing INT;
SELECT @id7_existing = ID FROM WEB_DROITS_ACCES WHERE ID_Section = 2 AND Action = 'EXPORT_PDF';

IF @id7_existing IS NOT NULL AND @id7_existing != 7
BEGIN
    -- Supprimer l'ID 7 s'il existe avec des valeurs incorrectes
    DELETE FROM WEB_DROITS_ACCES WHERE ID = 7 AND (ID_Section != 2 OR Action != 'EXPORT_PDF');
    -- Mettre à jour l'ID de l'enregistrement existant vers 7
    UPDATE WEB_DROITS_ACCES SET ID = 7, archive = 0 WHERE ID = @id7_existing;
    PRINT '  ✓ ID ' + CAST(@id7_existing AS VARCHAR) + ' modifié vers ID 7: ID_Section=2, Action=EXPORT_PDF';
END
ELSE IF @id7_existing = 7
BEGIN
    UPDATE WEB_DROITS_ACCES SET archive = 0 WHERE ID = 7;
    PRINT '  ✓ ID 7 déjà correct, archive = 0';
END
ELSE
BEGIN
    -- Vérifier si ID 7 existe avec des valeurs incorrectes
    IF EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID = 7)
    BEGIN
        UPDATE WEB_DROITS_ACCES SET ID_Section = 2, Action = 'EXPORT_PDF', archive = 0 WHERE ID = 7;
        PRINT '  ✓ ID 7 corrigé: ID_Section=2, Action=EXPORT_PDF';
    END
    ELSE
    BEGIN
        INSERT INTO WEB_DROITS_ACCES (ID, ID_Section, Action, archive) VALUES (7, 2, 'EXPORT_PDF', 0);
        PRINT '  + ID 7 créé: ID_Section=2, Action=EXPORT_PDF';
    END
END
PRINT '';

-- Correction ID 8: CONSULTATION, ID_Section=3
PRINT 'Correction ID 8: CONSULTATION, ID_Section=3';
DECLARE @id8_existing INT;
SELECT @id8_existing = ID FROM WEB_DROITS_ACCES WHERE ID_Section = 3 AND Action = 'CONSULTATION';

IF @id8_existing IS NOT NULL AND @id8_existing != 8
BEGIN
    -- Supprimer l'ID 8 s'il existe avec des valeurs incorrectes
    DELETE FROM WEB_DROITS_ACCES WHERE ID = 8 AND (ID_Section != 3 OR Action != 'CONSULTATION');
    -- Mettre à jour l'ID de l'enregistrement existant vers 8
    UPDATE WEB_DROITS_ACCES SET ID = 8, archive = 0 WHERE ID = @id8_existing;
    PRINT '  ✓ ID ' + CAST(@id8_existing AS VARCHAR) + ' modifié vers ID 8: ID_Section=3, Action=CONSULTATION';
END
ELSE IF @id8_existing = 8
BEGIN
    UPDATE WEB_DROITS_ACCES SET archive = 0 WHERE ID = 8;
    PRINT '  ✓ ID 8 déjà correct, archive = 0';
END
ELSE
BEGIN
    -- Vérifier si ID 8 existe avec des valeurs incorrectes
    IF EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID = 8)
    BEGIN
        UPDATE WEB_DROITS_ACCES SET ID_Section = 3, Action = 'CONSULTATION', archive = 0 WHERE ID = 8;
        PRINT '  ✓ ID 8 corrigé: ID_Section=3, Action=CONSULTATION';
    END
    ELSE
    BEGIN
        INSERT INTO WEB_DROITS_ACCES (ID, ID_Section, Action, archive) VALUES (8, 3, 'CONSULTATION', 0);
        PRINT '  + ID 8 créé: ID_Section=3, Action=CONSULTATION';
    END
END
PRINT '';

-- Vérifier l'état final
PRINT '================================================================================';
PRINT 'Etat final apres correction:';
PRINT '================================================================================';
SELECT ID, ID_Section, Action, archive 
FROM WEB_DROITS_ACCES 
WHERE ID IN (6, 7, 8)
ORDER BY ID;

PRINT '';
PRINT 'Termine';
GO
