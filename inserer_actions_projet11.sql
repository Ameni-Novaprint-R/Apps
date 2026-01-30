-- ================================================================================
-- INSERTION DES ACTIONS DU PROJET 11 DANS WEB_DROITS_ACCES
-- ================================================================================
USE novaprint_restored;
GO

PRINT 'Insertion des actions du Projet 11 dans WEB_DROITS_ACCES';
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

-- Section: Nouvelle fiche de production
DECLARE @ID_Section_Nouvelle INT;
SELECT @ID_Section_Nouvelle = ID FROM WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = 'Nouvelle fiche de production';

IF @ID_Section_Nouvelle IS NOT NULL
BEGIN
    PRINT '[Nouvelle fiche de production] (ID_Section=' + CAST(@ID_Section_Nouvelle AS VARCHAR) + ')';
    
    -- SAISIE
    INSERT INTO WEB_DROITS_ACCES (ID_Section, Action, archive)
    SELECT @ID_Section_Nouvelle, 'SAISIE', 0
    WHERE NOT EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Nouvelle AND Action = 'SAISIE');
    PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  + SAISIE' ELSE '  (deja presente) SAISIE' END;
    PRINT '';
END
ELSE
    PRINT '[WARN] Section "Nouvelle fiche de production" introuvable';
PRINT '';

-- Section: Liste des Traitements
DECLARE @ID_Section_Liste INT;
SELECT @ID_Section_Liste = ID FROM WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = 'Liste des Traitements';

IF @ID_Section_Liste IS NOT NULL
BEGIN
    PRINT '[Liste des Traitements] (ID_Section=' + CAST(@ID_Section_Liste AS VARCHAR) + ')';
    
    -- CONSULTATION
    INSERT INTO WEB_DROITS_ACCES (ID_Section, Action, archive)
    SELECT @ID_Section_Liste, 'CONSULTATION', 0
    WHERE NOT EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Liste AND Action = 'CONSULTATION');
    PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  + CONSULTATION' ELSE '  (deja presente) CONSULTATION' END;
    
    -- MODIFICATION
    INSERT INTO WEB_DROITS_ACCES (ID_Section, Action, archive)
    SELECT @ID_Section_Liste, 'MODIFICATION', 0
    WHERE NOT EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Liste AND Action = 'MODIFICATION');
    PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  + MODIFICATION' ELSE '  (deja presente) MODIFICATION' END;
    
    -- SUPPRESSION
    INSERT INTO WEB_DROITS_ACCES (ID_Section, Action, archive)
    SELECT @ID_Section_Liste, 'SUPPRESSION', 0
    WHERE NOT EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Liste AND Action = 'SUPPRESSION');
    PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  + SUPPRESSION' ELSE '  (deja presente) SUPPRESSION' END;
    
    -- SAISIE
    INSERT INTO WEB_DROITS_ACCES (ID_Section, Action, archive)
    SELECT @ID_Section_Liste, 'SAISIE', 0
    WHERE NOT EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Liste AND Action = 'SAISIE');
    PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  + SAISIE' ELSE '  (deja presente) SAISIE' END;
    PRINT '';
END
ELSE
    PRINT '[WARN] Section "Liste des Traitements" introuvable';
PRINT '';

-- Section: Statistiques
DECLARE @ID_Section_Stats INT;
SELECT @ID_Section_Stats = ID FROM WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = 'Statistiques';

IF @ID_Section_Stats IS NOT NULL
BEGIN
    PRINT '[Statistiques] (ID_Section=' + CAST(@ID_Section_Stats AS VARCHAR) + ')';
    
    -- CONSULTATION
    INSERT INTO WEB_DROITS_ACCES (ID_Section, Action, archive)
    SELECT @ID_Section_Stats, 'CONSULTATION', 0
    WHERE NOT EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Stats AND Action = 'CONSULTATION');
    PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  + CONSULTATION' ELSE '  (deja presente) CONSULTATION' END;
    
    -- EXPORT_EXCEL
    INSERT INTO WEB_DROITS_ACCES (ID_Section, Action, archive)
    SELECT @ID_Section_Stats, 'EXPORT_EXCEL', 0
    WHERE NOT EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Stats AND Action = 'EXPORT_EXCEL');
    PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  + EXPORT_EXCEL' ELSE '  (deja presente) EXPORT_EXCEL' END;
    
    -- EXPORT_PDF
    INSERT INTO WEB_DROITS_ACCES (ID_Section, Action, archive)
    SELECT @ID_Section_Stats, 'EXPORT_PDF', 0
    WHERE NOT EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Stats AND Action = 'EXPORT_PDF');
    PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  + EXPORT_PDF' ELSE '  (deja presente) EXPORT_PDF' END;
    PRINT '';
END
ELSE
    PRINT '[WARN] Section "Statistiques" introuvable';
PRINT '';

-- Récapitulatif
PRINT '================================================================================';
PRINT 'Recapitulatif';
PRINT '================================================================================';
SELECT 
    s.Nom AS Section,
    da.Action,
    CASE da.archive WHEN 0 THEN 'actif' ELSE 'archive' END AS Statut
FROM WEB_DROITS_ACCES da
INNER JOIN WEB_SECTIONS s ON s.ID = da.ID_Section
INNER JOIN WEB_PROJETS p ON p.ID = s.ID_Proj
WHERE p.NumProj = 11
ORDER BY s.Nom, da.Action;

PRINT '';
PRINT 'Termine';
GO
