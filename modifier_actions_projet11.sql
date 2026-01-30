-- ================================================================================
-- MODIFICATION DES ACTIONS DU PROJET 11 DANS WEB_DROITS_ACCES
-- ================================================================================
-- 1. Archiver EXPORT_EXCEL et EXPORT_PDF de la section Statistiques
-- 2. Ajouter EXPORT_EXCEL et EXPORT_PDF à la section Liste des Traitements
-- ================================================================================
USE novaprint_restored;
GO

PRINT 'Modification des actions du Projet 11 dans WEB_DROITS_ACCES';
PRINT '';

-- Récupérer l'ID du Projet 11
DECLARE @ID_Proj INT;
SELECT @ID_Proj = ID FROM WEB_PROJETS WHERE NumProj = 11;

IF @ID_Proj IS NULL
BEGIN
    PRINT 'ERREUR: Projet 11 introuvable dans WEB_PROJETS';
    RETURN;
END

PRINT 'Projet 11 trouve (ID=' + CAST(@ID_Proj AS VARCHAR) + ')';
PRINT '';

-- ================================================================================
-- ÉTAPE 1: Archiver EXPORT_EXCEL et EXPORT_PDF de Statistiques
-- ================================================================================
PRINT '[1] Archivage des actions EXPORT_EXCEL et EXPORT_PDF de la section Statistiques...';

DECLARE @ID_Section_Stats INT;
SELECT @ID_Section_Stats = ID FROM WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = 'Statistiques';

IF @ID_Section_Stats IS NOT NULL
BEGIN
    -- Archiver EXPORT_EXCEL
    UPDATE WEB_DROITS_ACCES 
    SET archive = 1 
    WHERE ID_Section = @ID_Section_Stats AND Action = 'EXPORT_EXCEL' AND archive = 0;
    PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  ✓ EXPORT_EXCEL archive (section Statistiques)' ELSE '  (deja archive ou absent) EXPORT_EXCEL' END;
    
    -- Archiver EXPORT_PDF
    UPDATE WEB_DROITS_ACCES 
    SET archive = 1 
    WHERE ID_Section = @ID_Section_Stats AND Action = 'EXPORT_PDF' AND archive = 0;
    PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  ✓ EXPORT_PDF archive (section Statistiques)' ELSE '  (deja archive ou absent) EXPORT_PDF' END;
END
ELSE
    PRINT '  [WARN] Section "Statistiques" introuvable';

PRINT '';

-- ================================================================================
-- ÉTAPE 2: Ajouter EXPORT_EXCEL et EXPORT_PDF à Liste des Traitements
-- ================================================================================
PRINT '[2] Ajout des actions EXPORT_EXCEL et EXPORT_PDF à la section Liste des Traitements...';

DECLARE @ID_Section_Liste INT;
SELECT @ID_Section_Liste = ID FROM WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = 'Liste des Traitements';

IF @ID_Section_Liste IS NOT NULL
BEGIN
    -- Ajouter EXPORT_EXCEL
    INSERT INTO WEB_DROITS_ACCES (ID_Section, Action, archive)
    SELECT @ID_Section_Liste, 'EXPORT_EXCEL', 0
    WHERE NOT EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Liste AND Action = 'EXPORT_EXCEL');
    PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  + EXPORT_EXCEL ajoute' ELSE '  (deja present) EXPORT_EXCEL' END;
    
    -- Ajouter EXPORT_PDF
    INSERT INTO WEB_DROITS_ACCES (ID_Section, Action, archive)
    SELECT @ID_Section_Liste, 'EXPORT_PDF', 0
    WHERE NOT EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Liste AND Action = 'EXPORT_PDF');
    PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  + EXPORT_PDF ajoute' ELSE '  (deja present) EXPORT_PDF' END;
END
ELSE
    PRINT '  [WARN] Section "Liste des Traitements" introuvable';

PRINT '';

-- ================================================================================
-- RÉCAPITULATIF
-- ================================================================================
PRINT '================================================================================';
PRINT 'Recapitulatif';
PRINT '================================================================================';

PRINT '';
PRINT 'Actions ACTIVES du Projet 11 dans WEB_DROITS_ACCES :';
SELECT 
    s.Nom AS Section,
    da.Action,
    CASE da.archive WHEN 0 THEN 'actif' ELSE 'archive' END AS Statut
FROM WEB_DROITS_ACCES da
INNER JOIN WEB_SECTIONS s ON s.ID = da.ID_Section
INNER JOIN WEB_PROJETS p ON p.ID = s.ID_Proj
WHERE p.NumProj = 11 AND da.archive = 0
ORDER BY s.Nom, da.Action;

PRINT '';
PRINT 'Actions ARCHIVEES du Projet 11 dans WEB_DROITS_ACCES :';
SELECT 
    s.Nom AS Section,
    da.Action,
    CASE da.archive WHEN 0 THEN 'actif' ELSE 'archive' END AS Statut
FROM WEB_DROITS_ACCES da
INNER JOIN WEB_SECTIONS s ON s.ID = da.ID_Section
INNER JOIN WEB_PROJETS p ON p.ID = s.ID_Proj
WHERE p.NumProj = 11 AND da.archive = 1
ORDER BY s.Nom, da.Action;

PRINT '';
PRINT 'Termine';
GO
