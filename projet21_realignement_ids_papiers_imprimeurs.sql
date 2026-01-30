-- ============================================================================
-- Script de Réalignement des IDs - PAPIERS_IMPRIMEURS
-- ============================================================================
-- Objectif: Réaligner les IDs de PAPIERS_IMPRIMEURS pour correspondre
--           exactement aux IDs de référence de la base Novaprint
--
-- IMPORTANT: Ce script doit être exécuté dans une transaction
--            avec possibilité de rollback en cas d'erreur
--
-- COMPLEXITÉ: Cette table a 4 relations directes (2 FK sortantes + 2 FK entrantes)
--             Nécessite une gestion plus prudente que PAPIERS_ARTICLES
-- ============================================================================

USE novaprint_restored;
GO

-- ============================================================================
-- ÉTAPE 1: VÉRIFICATIONS PRÉALABLES RENFORCÉES
-- ============================================================================

PRINT '=== ÉTAPE 1: Vérifications préalables renforcées ===';

-- Vérifier que les deux bases ont le même nombre d'enregistrements
DECLARE @count_source INT;
DECLARE @count_target INT;

SELECT @count_source = COUNT(*) FROM Novaprint.dbo.PAPIERS_IMPRIMEURS;
SELECT @count_target = COUNT(*) FROM novaprint_restored.dbo.PAPIERS_IMPRIMEURS;

IF @count_source <> @count_target
BEGIN
    PRINT '⚠ ATTENTION: Nombre d''enregistrements différent';
    PRINT '  Source: ' + CAST(@count_source AS VARCHAR);
    PRINT '  Cible: ' + CAST(@count_target AS VARCHAR);
    PRINT '  Les enregistrements supplémentaires en cible ne seront pas modifiés';
END
ELSE
BEGIN
    PRINT '✓ Nombre d''enregistrements identique';
END

-- Vérifier les références orphelines dans PAPIERS_TARIF_FMT
DECLARE @orphan_count_fmt INT;
SELECT @orphan_count_fmt = COUNT(*)
FROM novaprint_restored.dbo.PAPIERS_TARIF_FMT ptf
LEFT JOIN novaprint_restored.dbo.PAPIERS_IMPRIMEURS pi ON ptf.ID_PAPIMPRIM = pi.ID
WHERE ptf.ID_PAPIMPRIM IS NOT NULL AND pi.ID IS NULL;

IF @orphan_count_fmt > 0
BEGIN
    PRINT '⚠ ATTENTION: ' + CAST(@orphan_count_fmt AS VARCHAR) + ' références orphelines dans PAPIERS_TARIF_FMT';
    PRINT '  Ces références seront ignorées pendant le réalignement';
END
ELSE
BEGIN
    PRINT '✓ Aucune référence orpheline dans PAPIERS_TARIF_FMT';
END

-- Vérifier les références orphelines dans PAPIERS_TARIF_GRAM
DECLARE @orphan_count_gram INT;
SELECT @orphan_count_gram = COUNT(*)
FROM novaprint_restored.dbo.PAPIERS_TARIF_GRAM ptg
LEFT JOIN novaprint_restored.dbo.PAPIERS_IMPRIMEURS pi ON ptg.ID_PAPIMPRIM = pi.ID
WHERE ptg.ID_PAPIMPRIM IS NOT NULL AND pi.ID IS NULL;

IF @orphan_count_gram > 0
BEGIN
    PRINT '⚠ ATTENTION: ' + CAST(@orphan_count_gram AS VARCHAR) + ' références orphelines dans PAPIERS_TARIF_GRAM';
    PRINT '  Ces références seront ignorées pendant le réalignement';
END
ELSE
BEGIN
    PRINT '✓ Aucune référence orpheline dans PAPIERS_TARIF_GRAM';
END

-- ============================================================================
-- ÉTAPE 2: CRÉATION DE LA TABLE DE MAPPING
-- ============================================================================

PRINT '';
PRINT '=== ÉTAPE 2: Création de la table de mapping ===';

-- Supprimer la table de mapping si elle existe déjà
IF OBJECT_ID('tempdb..#ID_MAPPING_PAPIERS_IMPRIMEURS', 'U') IS NOT NULL
    DROP TABLE #ID_MAPPING_PAPIERS_IMPRIMEURS;

-- Créer la table de mapping temporaire
-- Cette table contient: ancien_ID (cible) -> nouveau_ID (source)
CREATE TABLE #ID_MAPPING_PAPIERS_IMPRIMEURS (
    ancien_ID INT NOT NULL,
    nouveau_ID INT NOT NULL,
    PRIMARY KEY (ancien_ID)
);

-- Remplir la table de mapping en comparant les données entre source et cible
-- Correspondance basée sur ID_PAPIER et ID_IMPRIMEUR (colonnes uniques)
INSERT INTO #ID_MAPPING_PAPIERS_IMPRIMEURS (ancien_ID, nouveau_ID)
SELECT 
    cible.ID AS ancien_ID,
    source.ID AS nouveau_ID
FROM novaprint_restored.dbo.PAPIERS_IMPRIMEURS cible
INNER JOIN Novaprint.dbo.PAPIERS_IMPRIMEURS source
    ON cible.ID_PAPIER = source.ID_PAPIER
    AND cible.ID_IMPRIMEUR = source.ID_IMPRIMEUR
WHERE cible.ID <> source.ID  -- Seulement les IDs qui diffèrent
    AND source.ID IS NOT NULL;

DECLARE @mapping_count INT;
SELECT @mapping_count = COUNT(*) FROM #ID_MAPPING_PAPIERS_IMPRIMEURS;

PRINT '✓ Table de mapping créée avec ' + CAST(@mapping_count AS VARCHAR) + ' correspondances';

IF @mapping_count = 0
BEGIN
    PRINT 'ℹ Aucun ID à réaligner - tous les IDs correspondent déjà';
    RETURN;
END

-- ============================================================================
-- ÉTAPE 3: VÉRIFICATION DES CONFLITS POTENTIELS
-- ============================================================================

PRINT '';
PRINT '=== ÉTAPE 3: Vérification des conflits potentiels ===';

-- Vérifier si les nouveaux IDs existent déjà dans la table cible
DECLARE @conflict_count INT;
SELECT @conflict_count = COUNT(*)
FROM #ID_MAPPING_PAPIERS_IMPRIMEURS m
INNER JOIN novaprint_restored.dbo.PAPIERS_IMPRIMEURS pi
    ON m.nouveau_ID = pi.ID
WHERE pi.ID NOT IN (SELECT ancien_ID FROM #ID_MAPPING_PAPIERS_IMPRIMEURS);

IF @conflict_count > 0
BEGIN
    RAISERROR('ERREUR: %d conflits d''IDs détectés. Les nouveaux IDs existent déjà dans la table cible.', 16, 1, @conflict_count);
    RETURN;
END

PRINT '✓ Aucun conflit d''IDs détecté';

-- ============================================================================
-- ÉTAPE 4: DÉMARRAGE DE LA TRANSACTION
-- ============================================================================

PRINT '';
PRINT '=== ÉTAPE 4: Démarrage de la transaction ===';

BEGIN TRANSACTION RealignementPAPIERS_IMPRIMEURS;

BEGIN TRY

    -- ============================================================================
    -- ÉTAPE 5: DÉSACTIVATION TEMPORAIRE DES CONTRAINTES FK ENTRANTES
    -- ============================================================================

    PRINT '';
    PRINT '=== ÉTAPE 5: Désactivation temporaire des contraintes FK entrantes ===';

    -- Désactiver la FK vers PAPIERS_TARIF_FMT
    ALTER TABLE PAPIERS_TARIF_FMT
    NOCHECK CONSTRAINT FK__PAPIERS_T__ID_PA__49659AB2;

    PRINT '✓ FK vers PAPIERS_TARIF_FMT désactivée';

    -- Désactiver la FK vers PAPIERS_TARIF_GRAM
    ALTER TABLE PAPIERS_TARIF_GRAM
    NOCHECK CONSTRAINT FK__PAPIERS_T__ID_PA__4A59BEEB;

    PRINT '✓ FK vers PAPIERS_TARIF_GRAM désactivée';

    -- ============================================================================
    -- ÉTAPE 6: MISE À JOUR DES RÉFÉRENCES DANS PAPIERS_TARIF_FMT
    -- ============================================================================

    PRINT '';
    PRINT '=== ÉTAPE 6: Mise à jour des références dans PAPIERS_TARIF_FMT ===';

    -- Vérifier les conflits potentiels
    DECLARE @conflict_count_fmt INT;
    SELECT @conflict_count_fmt = COUNT(*)
    FROM (
        SELECT 
            ptf.ID_ARTICLE,
            ptf.PaqCalcul,
            m.nouveau_ID,
            COUNT(*) AS nb_lignes
        FROM novaprint_restored.dbo.PAPIERS_TARIF_FMT ptf
        INNER JOIN #ID_MAPPING_PAPIERS_IMPRIMEURS m ON ptf.ID_PAPIMPRIM = m.ancien_ID
        WHERE ptf.ID_PAPIMPRIM IS NOT NULL
        GROUP BY ptf.ID_ARTICLE, ptf.PaqCalcul, m.nouveau_ID
        HAVING COUNT(*) > 1
    ) AS conflicts;

    IF @conflict_count_fmt > 0
    BEGIN
        PRINT '⚠ ATTENTION: ' + CAST(@conflict_count_fmt AS VARCHAR) + ' conflits potentiels détectés';
        PRINT 'Les lignes en conflit seront ignorées pour éviter les doublons';
    END

    -- Mettre à jour les références FK dans PAPIERS_TARIF_FMT
    -- En excluant les lignes qui créeraient des conflits de clé primaire
    UPDATE ptf
    SET ID_PAPIMPRIM = m.nouveau_ID
    FROM novaprint_restored.dbo.PAPIERS_TARIF_FMT ptf
    INNER JOIN #ID_MAPPING_PAPIERS_IMPRIMEURS m ON ptf.ID_PAPIMPRIM = m.ancien_ID
    WHERE ptf.ID_PAPIMPRIM IS NOT NULL
        -- Exclure les lignes qui créeraient des doublons de clé primaire
        AND NOT EXISTS (
            SELECT 1
            FROM novaprint_restored.dbo.PAPIERS_TARIF_FMT ptf2
            INNER JOIN #ID_MAPPING_PAPIERS_IMPRIMEURS m2 ON ptf2.ID_PAPIMPRIM = m2.ancien_ID
            WHERE ptf2.ID_ARTICLE = ptf.ID_ARTICLE
                AND ptf2.PaqCalcul = ptf.PaqCalcul
                AND m2.nouveau_ID = m.nouveau_ID
                AND ptf2.ID_PAPIMPRIM <> ptf.ID_PAPIMPRIM
        );

    DECLARE @fk_updated_count_fmt INT;
    SELECT @fk_updated_count_fmt = @@ROWCOUNT;

    PRINT '✓ ' + CAST(@fk_updated_count_fmt AS VARCHAR) + ' références mises à jour dans PAPIERS_TARIF_FMT';

    -- ============================================================================
    -- ÉTAPE 7: MISE À JOUR DES RÉFÉRENCES DANS PAPIERS_TARIF_GRAM
    -- ============================================================================

    PRINT '';
    PRINT '=== ÉTAPE 7: Mise à jour des références dans PAPIERS_TARIF_GRAM ===';

    -- Mettre à jour les références FK dans PAPIERS_TARIF_GRAM
    UPDATE novaprint_restored.dbo.PAPIERS_TARIF_GRAM
    SET ID_PAPIMPRIM = m.nouveau_ID
    FROM novaprint_restored.dbo.PAPIERS_TARIF_GRAM ptg
    INNER JOIN #ID_MAPPING_PAPIERS_IMPRIMEURS m ON ptg.ID_PAPIMPRIM = m.ancien_ID
    WHERE ptg.ID_PAPIMPRIM IS NOT NULL;

    DECLARE @fk_updated_count_gram INT;
    SELECT @fk_updated_count_gram = @@ROWCOUNT;

    PRINT '✓ ' + CAST(@fk_updated_count_gram AS VARCHAR) + ' références mises à jour dans PAPIERS_TARIF_GRAM';

    -- ============================================================================
    -- ÉTAPE 8: DÉSACTIVATION TEMPORAIRE DE IDENTITY
    -- ============================================================================

    PRINT '';
    PRINT '=== ÉTAPE 8: Désactivation temporaire de IDENTITY ===';

    -- Sauvegarder la valeur actuelle de IDENTITY
    DECLARE @current_seed BIGINT;
    SELECT @current_seed = CAST(IDENT_CURRENT('dbo.PAPIERS_IMPRIMEURS') AS BIGINT);

    PRINT 'Valeur actuelle de IDENTITY: ' + CAST(@current_seed AS VARCHAR);

    -- Désactiver IDENTITY pour permettre la modification manuelle des IDs
    SET IDENTITY_INSERT dbo.PAPIERS_IMPRIMEURS ON;

    PRINT '✓ IDENTITY désactivé temporairement';

    -- ============================================================================
    -- ÉTAPE 9: MISE À JOUR DES IDs DANS PAPIERS_IMPRIMEURS
    -- ============================================================================

    PRINT '';
    PRINT '=== ÉTAPE 9: Mise à jour des IDs dans PAPIERS_IMPRIMEURS ===';

    -- Utiliser une table temporaire pour stocker les données à mettre à jour
    IF OBJECT_ID('tempdb..#TEMP_UPDATE_PAPIERS_IMPRIMEURS', 'U') IS NOT NULL
        DROP TABLE #TEMP_UPDATE_PAPIERS_IMPRIMEURS;

    -- Créer une table temporaire avec toutes les colonnes de PAPIERS_IMPRIMEURS
    SELECT * INTO #TEMP_UPDATE_PAPIERS_IMPRIMEURS
    FROM novaprint_restored.dbo.PAPIERS_IMPRIMEURS
    WHERE ID IN (SELECT ancien_ID FROM #ID_MAPPING_PAPIERS_IMPRIMEURS);

    -- Mettre à jour les IDs dans la table temporaire
    UPDATE #TEMP_UPDATE_PAPIERS_IMPRIMEURS
    SET ID = m.nouveau_ID
    FROM #TEMP_UPDATE_PAPIERS_IMPRIMEURS t
    INNER JOIN #ID_MAPPING_PAPIERS_IMPRIMEURS m ON t.ID = m.ancien_ID;

    -- Supprimer les anciens enregistrements
    DELETE FROM novaprint_restored.dbo.PAPIERS_IMPRIMEURS
    WHERE ID IN (SELECT ancien_ID FROM #ID_MAPPING_PAPIERS_IMPRIMEURS);

    -- Insérer les enregistrements avec les nouveaux IDs
    INSERT INTO novaprint_restored.dbo.PAPIERS_IMPRIMEURS
    SELECT * FROM #TEMP_UPDATE_PAPIERS_IMPRIMEURS;

    DECLARE @updated_count INT;
    SELECT @updated_count = @@ROWCOUNT;

    PRINT '✓ ' + CAST(@updated_count AS VARCHAR) + ' IDs mis à jour dans PAPIERS_IMPRIMEURS';

    -- ============================================================================
    -- ÉTAPE 10: RÉACTIVATION DE IDENTITY
    -- ============================================================================

    PRINT '';
    PRINT '=== ÉTAPE 10: Réactivation de IDENTITY ===';

    SET IDENTITY_INSERT dbo.PAPIERS_IMPRIMEURS OFF;

    -- Réinitialiser IDENTITY avec une nouvelle seed basée sur le max ID actuel
    DECLARE @max_id INT;
    SELECT @max_id = ISNULL(MAX(ID), 0) FROM novaprint_restored.dbo.PAPIERS_IMPRIMEURS;

    DBCC CHECKIDENT ('dbo.PAPIERS_IMPRIMEURS', RESEED, @max_id);

    PRINT '✓ IDENTITY réactivé avec seed: ' + CAST(@max_id AS VARCHAR);

    -- ============================================================================
    -- ÉTAPE 11: RÉACTIVATION DES CONTRAINTES FK ENTRANTES
    -- ============================================================================

    PRINT '';
    PRINT '=== ÉTAPE 11: Réactivation des contraintes FK entrantes ===';

    -- Réactiver la FK vers PAPIERS_TARIF_FMT
    ALTER TABLE PAPIERS_TARIF_FMT
    CHECK CONSTRAINT FK__PAPIERS_T__ID_PA__49659AB2;

    PRINT '✓ FK vers PAPIERS_TARIF_FMT réactivée';

    -- Réactiver la FK vers PAPIERS_TARIF_GRAM
    ALTER TABLE PAPIERS_TARIF_GRAM
    CHECK CONSTRAINT FK__PAPIERS_T__ID_PA__4A59BEEB;

    PRINT '✓ FK vers PAPIERS_TARIF_GRAM réactivée';

    -- ============================================================================
    -- ÉTAPE 12: VÉRIFICATIONS POST-TRAITEMENT
    -- ============================================================================

    PRINT '';
    PRINT '=== ÉTAPE 12: Vérifications post-traitement ===';

    -- Vérifier que tous les IDs correspondent maintenant
    DECLARE @mismatch_count INT;
    SELECT @mismatch_count = COUNT(*)
    FROM novaprint_restored.dbo.PAPIERS_IMPRIMEURS cible
    INNER JOIN Novaprint.dbo.PAPIERS_IMPRIMEURS source
        ON cible.ID_PAPIER = source.ID_PAPIER
        AND cible.ID_IMPRIMEUR = source.ID_IMPRIMEUR
    WHERE cible.ID <> source.ID;

    IF @mismatch_count > 0
    BEGIN
        PRINT '⚠ ATTENTION: ' + CAST(@mismatch_count AS VARCHAR) + ' IDs ne correspondent toujours pas après le traitement';
    END
    ELSE
    BEGIN
        PRINT '✓ Tous les IDs correspondent maintenant';
    END

    -- Vérifier l'intégrité référentielle dans PAPIERS_TARIF_FMT
    DECLARE @orphan_after_fmt INT;
    SELECT @orphan_after_fmt = COUNT(*)
    FROM novaprint_restored.dbo.PAPIERS_TARIF_FMT ptf
    LEFT JOIN novaprint_restored.dbo.PAPIERS_IMPRIMEURS pi ON ptf.ID_PAPIMPRIM = pi.ID
    WHERE ptf.ID_PAPIMPRIM IS NOT NULL AND pi.ID IS NULL;

    IF @orphan_after_fmt > 0
    BEGIN
        PRINT '⚠ ATTENTION: ' + CAST(@orphan_after_fmt AS VARCHAR) + ' références orphelines restantes dans PAPIERS_TARIF_FMT';
    END
    ELSE
    BEGIN
        PRINT '✓ Intégrité référentielle vérifiée dans PAPIERS_TARIF_FMT - aucune référence orpheline';
    END

    -- Vérifier l'intégrité référentielle dans PAPIERS_TARIF_GRAM
    DECLARE @orphan_after_gram INT;
    SELECT @orphan_after_gram = COUNT(*)
    FROM novaprint_restored.dbo.PAPIERS_TARIF_GRAM ptg
    LEFT JOIN novaprint_restored.dbo.PAPIERS_IMPRIMEURS pi ON ptg.ID_PAPIMPRIM = pi.ID
    WHERE ptg.ID_PAPIMPRIM IS NOT NULL AND pi.ID IS NULL;

    IF @orphan_after_gram > 0
    BEGIN
        PRINT '⚠ ATTENTION: ' + CAST(@orphan_after_gram AS VARCHAR) + ' références orphelines restantes dans PAPIERS_TARIF_GRAM';
    END
    ELSE
    BEGIN
        PRINT '✓ Intégrité référentielle vérifiée dans PAPIERS_TARIF_GRAM - aucune référence orpheline';
    END

    -- ============================================================================
    -- VALIDATION DE LA TRANSACTION
    -- ============================================================================

    COMMIT TRANSACTION RealignementPAPIERS_IMPRIMEURS;

    PRINT '';
    PRINT '=== RÉSUMÉ FINAL ===';
    PRINT 'IDs réalisés: ' + CAST(@mapping_count AS VARCHAR);
    PRINT 'Références FK mises à jour dans PAPIERS_TARIF_FMT: ' + CAST(@fk_updated_count_fmt AS VARCHAR);
    PRINT 'Références FK mises à jour dans PAPIERS_TARIF_GRAM: ' + CAST(@fk_updated_count_gram AS VARCHAR);
    PRINT 'Traitement terminé avec succès!';

END TRY
BEGIN CATCH
    -- En cas d'erreur, rollback de la transaction
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION RealignementPAPIERS_IMPRIMEURS;

    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
    DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
    DECLARE @ErrorState INT = ERROR_STATE();

    PRINT '';
    PRINT '=== ERREUR DÉTECTÉE - ROLLBACK EFFECTUÉ ===';
    PRINT 'Message: ' + @ErrorMessage;
    PRINT 'Sévérité: ' + CAST(@ErrorSeverity AS VARCHAR);
    PRINT 'État: ' + CAST(@ErrorState AS VARCHAR);

    RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState);
END CATCH

-- Nettoyage
IF OBJECT_ID('tempdb..#ID_MAPPING_PAPIERS_IMPRIMEURS', 'U') IS NOT NULL
    DROP TABLE #ID_MAPPING_PAPIERS_IMPRIMEURS;

IF OBJECT_ID('tempdb..#TEMP_UPDATE_PAPIERS_IMPRIMEURS', 'U') IS NOT NULL
    DROP TABLE #TEMP_UPDATE_PAPIERS_IMPRIMEURS;

GO
