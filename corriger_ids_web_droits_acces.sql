-- ================================================================================
-- CORRECTION DES IDs SPECIFIQUES DANS WEB_DROITS_ACCES
-- ================================================================================
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
WHERE ID IN (6, 7, 8)
ORDER BY ID;
PRINT '';

-- Correction ID 6
PRINT 'Correction ID 6: EXPORT_EXCEL, ID_Section=2';
UPDATE WEB_DROITS_ACCES 
SET ID_Section = 2, Action = 'EXPORT_EXCEL', archive = 0
WHERE ID = 6;
PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  ✓ ID 6 corrigé' ELSE '  (ID 6 n''existe pas ou déjà correct)' END;
PRINT '';

-- Correction ID 7
PRINT 'Correction ID 7: EXPORT_PDF, ID_Section=2';
UPDATE WEB_DROITS_ACCES 
SET ID_Section = 2, Action = 'EXPORT_PDF', archive = 0
WHERE ID = 7;
PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  ✓ ID 7 corrigé' ELSE '  (ID 7 n''existe pas ou déjà correct)' END;
PRINT '';

-- Correction ID 8
PRINT 'Correction ID 8: CONSULTATION, ID_Section=3';
UPDATE WEB_DROITS_ACCES 
SET ID_Section = 3, Action = 'CONSULTATION', archive = 0
WHERE ID = 8;
PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  ✓ ID 8 corrigé' ELSE '  (ID 8 n''existe pas ou déjà correct)' END;
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
