-- ============================================================================
-- Script de Réalignement des IDs - PAPIERS_ARTICLES
-- ============================================================================
-- Objectif: Réaligner les IDs de PAPIERS_ARTICLES pour correspondre
--           exactement aux IDs de référence de la base Novaprint
--
-- IMPORTANT: Ce script doit être exécuté dans une transaction
--            avec possibilité de rollback en cas d'erreur
-- ============================================================================

USE novaprint_restored;
GO

-- ============================================================================
-- ÉTAPE 1: VÉRIFICATIONS PRÉALABLES
-- ============================================================================

PRINT '=== ÉTAPE 1: Vérifications préalables ===';

-- Vérifier que les deux bases ont le même nombre d'enregistrements
DECLARE @count_source INT;
DECLARE @count_target INT;

SELECT @count_source = COUNT(*) FROM Novaprint.dbo.PAPIERS_ARTICLES;
SELECT @count_target = COUNT(*) FROM novaprint_restored.dbo.PAPIERS_ARTICLES;

IF @count_source <> @count_target
BEGIN
    RAISERROR('ERREUR: Nombre d''enregistrements différent (Source: %d, Cible: %d)', 16, 1, @count_source, @count_target);
    RETURN;
END

PRINT '✓ Nombre d''enregistrements identique';

-- Vérifier les références orphelines avant traitement
DECLARE @orphan_count INT;
SELECT @orphan_count = COUNT(*)
FROM novaprint_restored.dbo.PAPIERS_TARIF_FMT ptf
LEFT JOIN novaprint_restored.dbo.PAPIERS_ARTICLES pa ON ptf.ID_ARTICLE = pa.ID
WHERE ptf.ID_ARTICLE IS NOT NULL AND pa.ID IS NULL;

IF @orphan_count > 0
BEGIN
    PRINT '⚠ ATTENTION: ' + CAST(@orphan_count AS VARCHAR) + ' références orphelines détectées';
    PRINT 'Ces références seront ignorées pendant le réalignement';
END
ELSE
BEGIN
    PRINT '✓ Aucune référence orpheline détectée';
END

-- ============================================================================
-- ÉTAPE 2: CRÉATION DE LA TABLE DE MAPPING
-- ============================================================================

PRINT '';
PRINT '=== ÉTAPE 2: Création de la table de mapping ===';

-- Supprimer la table de mapping si elle existe déjà
IF OBJECT_ID('tempdb..#ID_MAPPING_PAPIERS_ARTICLES', 'U') IS NOT NULL
    DROP TABLE #ID_MAPPING_PAPIERS_ARTICLES;

-- Créer la table de mapping temporaire
-- Cette table contient: ancien_ID (cible) -> nouveau_ID (source)
CREATE TABLE #ID_MAPPING_PAPIERS_ARTICLES (
    ancien_ID INT NOT NULL,
    nouveau_ID INT NOT NULL,
    PRIMARY KEY (ancien_ID)
);

-- Remplir la table de mapping en comparant les données entre source et cible
-- On utilise un critère de correspondance basé sur des colonnes uniques
-- (à adapter selon la structure réelle de la table)
INSERT INTO #ID_MAPPING_PAPIERS_ARTICLES (ancien_ID, nouveau_ID)
SELECT 
    cible.ID AS ancien_ID,
    source.ID AS nouveau_ID
FROM novaprint_restored.dbo.PAPIERS_ARTICLES cible
INNER JOIN Novaprint.dbo.PAPIERS_ARTICLES source
    -- Correspondance basée sur des colonnes uniques (à adapter)
    -- Exemple: si vous avez une colonne CODE ou LIBELLE unique
    ON cible.ID_PAPIER = source.ID_PAPIER
    AND cible.ID_CERTIFICATION = source.ID_CERTIFICATION
    -- Ajouter d'autres critères de correspondance si nécessaire
WHERE cible.ID <> source.ID  -- Seulement les IDs qui diffèrent
    AND source.ID IS NOT NULL;

DECLARE @mapping_count INT;
SELECT @mapping_count = COUNT(*) FROM #ID_MAPPING_PAPIERS_ARTICLES;

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
FROM #ID_MAPPING_PAPIERS_ARTICLES m
INNER JOIN novaprint_restored.dbo.PAPIERS_ARTICLES pa
    ON m.nouveau_ID = pa.ID
WHERE pa.ID NOT IN (SELECT ancien_ID FROM #ID_MAPPING_PAPIERS_ARTICLES);

IF @conflict_count > 0
BEGIN
    RAISERROR('ERREUR: %d conflits d''IDs détectés. Les nouveaux IDs existent déjà dans la table cible.', 16, 1, @conflict_count);
    RETURN;
END

PRINT '✓ Aucun conflit d''IDs détecté';

-- ============================================================================
-- ÉTAPE 4: DÉSACTIVATION TEMPORAIRE DE IDENTITY
-- ============================================================================

PRINT '';
PRINT '=== ÉTAPE 4: Désactivation temporaire de IDENTITY ===';

-- Sauvegarder la valeur actuelle de IDENTITY
DECLARE @current_seed BIGINT;
SELECT @current_seed = CAST(IDENT_CURRENT('dbo.PAPIERS_ARTICLES') AS BIGINT);

PRINT 'Valeur actuelle de IDENTITY: ' + CAST(@current_seed AS VARCHAR);

-- Désactiver IDENTITY pour permettre la modification manuelle des IDs
-- Note: Cette opération nécessite des permissions élevées
SET IDENTITY_INSERT dbo.PAPIERS_ARTICLES ON;

PRINT '✓ IDENTITY désactivé temporairement';

-- ============================================================================
-- ÉTAPE 5: MISE À JOUR DES IDs DANS PAPIERS_ARTICLES
-- ============================================================================

PRINT '';
PRINT '=== ÉTAPE 5: Mise à jour des IDs dans PAPIERS_ARTICLES ===';

-- Utiliser une table temporaire pour stocker les données à mettre à jour
IF OBJECT_ID('tempdb..#TEMP_UPDATE_PAPIERS_ARTICLES', 'U') IS NOT NULL
    DROP TABLE #TEMP_UPDATE_PAPIERS_ARTICLES;

-- Créer une table temporaire avec toutes les colonnes de PAPIERS_ARTICLES
SELECT * INTO #TEMP_UPDATE_PAPIERS_ARTICLES
FROM novaprint_restored.dbo.PAPIERS_ARTICLES
WHERE ID IN (SELECT ancien_ID FROM #ID_MAPPING_PAPIERS_ARTICLES);

-- Mettre à jour les IDs dans la table temporaire
UPDATE #TEMP_UPDATE_PAPIERS_ARTICLES
SET ID = m.nouveau_ID
FROM #TEMP_UPDATE_PAPIERS_ARTICLES t
INNER JOIN #ID_MAPPING_PAPIERS_ARTICLES m ON t.ID = m.ancien_ID;

-- Supprimer les anciens enregistrements
DELETE FROM novaprint_restored.dbo.PAPIERS_ARTICLES
WHERE ID IN (SELECT ancien_ID FROM #ID_MAPPING_PAPIERS_ARTICLES);

-- Insérer les enregistrements avec les nouveaux IDs
INSERT INTO novaprint_restored.dbo.PAPIERS_ARTICLES
SELECT * FROM #TEMP_UPDATE_PAPIERS_ARTICLES;

DECLARE @updated_count INT;
SELECT @updated_count = @@ROWCOUNT;

PRINT '✓ ' + CAST(@updated_count AS VARCHAR) + ' IDs mis à jour dans PAPIERS_ARTICLES';

-- ============================================================================
-- ÉTAPE 6: MISE À JOUR DES RÉFÉRENCES DANS PAPIERS_TARIF_FMT
-- ============================================================================

PRINT '';
PRINT '=== ÉTAPE 6: Mise à jour des références dans PAPIERS_TARIF_FMT ===';

-- Mettre à jour les références FK dans PAPIERS_TARIF_FMT
UPDATE novaprint_restored.dbo.PAPIERS_TARIF_FMT
SET ID_ARTICLE = m.nouveau_ID
FROM novaprint_restored.dbo.PAPIERS_TARIF_FMT ptf
INNER JOIN #ID_MAPPING_PAPIERS_ARTICLES m ON ptf.ID_ARTICLE = m.ancien_ID
WHERE ptf.ID_ARTICLE IS NOT NULL;

DECLARE @fk_updated_count INT;
SELECT @fk_updated_count = @@ROWCOUNT;

PRINT '✓ ' + CAST(@fk_updated_count AS VARCHAR) + ' références mises à jour dans PAPIERS_TARIF_FMT';

-- ============================================================================
-- ÉTAPE 7: RÉACTIVATION DE IDENTITY
-- ============================================================================

PRINT '';
PRINT '=== ÉTAPE 7: Réactivation de IDENTITY ===';

SET IDENTITY_INSERT dbo.PAPIERS_ARTICLES OFF;

-- Réinitialiser IDENTITY avec une nouvelle seed basée sur le max ID actuel
DECLARE @max_id INT;
SELECT @max_id = ISNULL(MAX(ID), 0) FROM novaprint_restored.dbo.PAPIERS_ARTICLES;

DBCC CHECKIDENT ('dbo.PAPIERS_ARTICLES', RESEED, @max_id);

PRINT '✓ IDENTITY réactivé avec seed: ' + CAST(@max_id AS VARCHAR);

-- ============================================================================
-- ÉTAPE 8: VÉRIFICATIONS POST-TRAITEMENT
-- ============================================================================

PRINT '';
PRINT '=== ÉTAPE 8: Vérifications post-traitement ===';

-- Vérifier que tous les IDs correspondent maintenant
DECLARE @mismatch_count INT;
SELECT @mismatch_count = COUNT(*)
FROM novaprint_restored.dbo.PAPIERS_ARTICLES cible
INNER JOIN Novaprint.dbo.PAPIERS_ARTICLES source
    ON cible.ID_PAPIER = source.ID_PAPIER
    AND cible.ID_CERTIFICATION = source.ID_CERTIFICATION
WHERE cible.ID <> source.ID;

IF @mismatch_count > 0
BEGIN
    RAISERROR('ATTENTION: %d IDs ne correspondent toujours pas après le traitement', 10, 1, @mismatch_count);
END
ELSE
BEGIN
    PRINT '✓ Tous les IDs correspondent maintenant';
END

-- Vérifier l'intégrité référentielle
DECLARE @orphan_after INT;
SELECT @orphan_after = COUNT(*)
FROM novaprint_restored.dbo.PAPIERS_TARIF_FMT ptf
LEFT JOIN novaprint_restored.dbo.PAPIERS_ARTICLES pa ON ptf.ID_ARTICLE = pa.ID
WHERE ptf.ID_ARTICLE IS NOT NULL AND pa.ID IS NULL;

IF @orphan_after > 0
BEGIN
    PRINT '⚠ ATTENTION: ' + CAST(@orphan_after AS VARCHAR) + ' références orphelines restantes';
END
ELSE
BEGIN
    PRINT '✓ Intégrité référentielle vérifiée - aucune référence orpheline';
END

-- ============================================================================
-- RÉSUMÉ FINAL
-- ============================================================================

PRINT '';
PRINT '=== RÉSUMÉ FINAL ===';
PRINT 'IDs réalisés: ' + CAST(@mapping_count AS VARCHAR);
PRINT 'Références FK mises à jour: ' + CAST(@fk_updated_count AS VARCHAR);
PRINT 'Traitement terminé avec succès!';

-- Nettoyage
DROP TABLE #ID_MAPPING_PAPIERS_ARTICLES;
DROP TABLE #TEMP_UPDATE_PAPIERS_ARTICLES;

GO
