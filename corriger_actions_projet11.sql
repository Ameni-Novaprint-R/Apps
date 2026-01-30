-- ================================================================================
-- CORRECTION DES ACTIONS DU PROJET 11 DANS WEB_DROITS_ACCES
-- ================================================================================
-- Configuration finale attendue :
-- 1. Section: Nouvelle fiche de production (ID_Section=1)
--    - SAISIE
-- 2. Section: Liste des Traitements (ID_Section=2)
--    - CONSULTATION
--    - MODIFICATION
--    - SUPPRESSION
--    - SAISIE
--    - EXPORT_EXCEL
--    - EXPORT_PDF
-- 3. Section: Statistiques (ID_Section=3)
--    - CONSULTATION
-- ================================================================================
USE novaprint_restored;
GO

PRINT 'Correction des actions du Projet 11 dans WEB_DROITS_ACCES';
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
-- SECTION 1: Nouvelle fiche de production
-- ================================================================================
PRINT '[1] Section: Nouvelle fiche de production';
DECLARE @ID_Section_Nouvelle INT;
SELECT @ID_Section_Nouvelle = ID FROM WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = 'Nouvelle fiche de production';

IF @ID_Section_Nouvelle IS NOT NULL
BEGIN
    -- Archiver toutes les actions sauf SAISIE
    UPDATE WEB_DROITS_ACCES SET archive = 1 
    WHERE ID_Section = @ID_Section_Nouvelle AND Action != 'SAISIE' AND archive = 0;
    
    -- S'assurer que SAISIE existe et est active
    IF NOT EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Nouvelle AND Action = 'SAISIE')
    BEGIN
        INSERT INTO WEB_DROITS_ACCES (ID_Section, Action, archive) VALUES (@ID_Section_Nouvelle, 'SAISIE', 0);
        PRINT '  + SAISIE ajoute';
    END
    ELSE IF EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Nouvelle AND Action = 'SAISIE' AND archive = 1)
    BEGIN
        UPDATE WEB_DROITS_ACCES SET archive = 0 WHERE ID_Section = @ID_Section_Nouvelle AND Action = 'SAISIE';
        PRINT '  ✓ SAISIE reactive';
    END
    ELSE
        PRINT '  (deja actif) SAISIE';
END
ELSE
    PRINT '  [WARN] Section "Nouvelle fiche de production" introuvable';
PRINT '';

-- ================================================================================
-- SECTION 2: Liste des Traitements
-- ================================================================================
PRINT '[2] Section: Liste des Traitements';
DECLARE @ID_Section_Liste INT;
SELECT @ID_Section_Liste = ID FROM WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = 'Liste des Traitements';

IF @ID_Section_Liste IS NOT NULL
BEGIN
    -- Actions attendues
    DECLARE @Actions_Liste TABLE (Action NVARCHAR(100));
    INSERT INTO @Actions_Liste VALUES ('CONSULTATION'), ('MODIFICATION'), ('SUPPRESSION'), ('SAISIE'), ('EXPORT_EXCEL'), ('EXPORT_PDF');
    
    -- Archiver les actions non attendues
    UPDATE WEB_DROITS_ACCES SET archive = 1 
    WHERE ID_Section = @ID_Section_Liste 
    AND Action NOT IN (SELECT Action FROM @Actions_Liste) 
    AND archive = 0;
    
    -- Ajouter/Réactiver les actions attendues
    DECLARE @Action_Liste NVARCHAR(100);
    DECLARE action_cursor CURSOR FOR SELECT Action FROM @Actions_Liste;
    OPEN action_cursor;
    FETCH NEXT FROM action_cursor INTO @Action_Liste;
    
    WHILE @@FETCH_STATUS = 0
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Liste AND Action = @Action_Liste)
        BEGIN
            INSERT INTO WEB_DROITS_ACCES (ID_Section, Action, archive) VALUES (@ID_Section_Liste, @Action_Liste, 0);
            PRINT '  + ' + @Action_Liste + ' ajoute';
        END
        ELSE IF EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Liste AND Action = @Action_Liste AND archive = 1)
        BEGIN
            UPDATE WEB_DROITS_ACCES SET archive = 0 WHERE ID_Section = @ID_Section_Liste AND Action = @Action_Liste;
            PRINT '  ✓ ' + @Action_Liste + ' reactive';
        END
        ELSE
            PRINT '  (deja actif) ' + @Action_Liste;
        
        FETCH NEXT FROM action_cursor INTO @Action_Liste;
    END
    
    CLOSE action_cursor;
    DEALLOCATE action_cursor;
END
ELSE
    PRINT '  [WARN] Section "Liste des Traitements" introuvable';
PRINT '';

-- ================================================================================
-- SECTION 3: Statistiques
-- ================================================================================
PRINT '[3] Section: Statistiques';
DECLARE @ID_Section_Stats INT;
SELECT @ID_Section_Stats = ID FROM WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = 'Statistiques';

IF @ID_Section_Stats IS NOT NULL
BEGIN
    -- Archiver toutes les actions sauf CONSULTATION
    UPDATE WEB_DROITS_ACCES SET archive = 1 
    WHERE ID_Section = @ID_Section_Stats AND Action != 'CONSULTATION' AND archive = 0;
    
    -- S'assurer que CONSULTATION existe et est active
    IF NOT EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Stats AND Action = 'CONSULTATION')
    BEGIN
        INSERT INTO WEB_DROITS_ACCES (ID_Section, Action, archive) VALUES (@ID_Section_Stats, 'CONSULTATION', 0);
        PRINT '  + CONSULTATION ajoute';
    END
    ELSE IF EXISTS (SELECT 1 FROM WEB_DROITS_ACCES WHERE ID_Section = @ID_Section_Stats AND Action = 'CONSULTATION' AND archive = 1)
    BEGIN
        UPDATE WEB_DROITS_ACCES SET archive = 0 WHERE ID_Section = @ID_Section_Stats AND Action = 'CONSULTATION';
        PRINT '  ✓ CONSULTATION reactive';
    END
    ELSE
        PRINT '  (deja actif) CONSULTATION';
END
ELSE
    PRINT '  [WARN] Section "Statistiques" introuvable';
PRINT '';

-- ================================================================================
-- RÉCAPITULATIF
-- ================================================================================
PRINT '================================================================================';
PRINT 'Recapitulatif - Actions ACTIVES du Projet 11';
PRINT '================================================================================';
SELECT 
    s.Nom AS Section,
    da.Action
FROM WEB_DROITS_ACCES da
INNER JOIN WEB_SECTIONS s ON s.ID = da.ID_Section
INNER JOIN WEB_PROJETS p ON p.ID = s.ID_Proj
WHERE p.NumProj = 11 AND da.archive = 0
ORDER BY s.Nom, da.Action;

PRINT '';
PRINT 'Termine';
GO
