-- ============================================================================
-- Script de Réactivation de la Confiance des Contraintes FK
-- Table: PAPIERS_IMPRIMEURS
-- ============================================================================
-- Objectif: Réactiver la confiance des contraintes FK après le réalignement
--           pour que SQL Server les considère comme vérifiées
-- ============================================================================

USE novaprint_restored;
GO

PRINT '============================================================================';
PRINT 'REACTIVATION DE LA CONFIANCE DES CONTRAINTES FK';
PRINT 'Table: PAPIERS_IMPRIMEURS';
PRINT '============================================================================';
PRINT '';

-- ============================================================================
-- ÉTAPE 1: Réactivation des Contraintes FK Sortantes
-- ============================================================================

PRINT '=== ÉTAPE 1: Réactivation des contraintes FK sortantes ===';
PRINT '';

-- Vers IMPRIMEURS
PRINT 'Réactivation FK vers IMPRIMEURS...';
ALTER TABLE PAPIERS_IMPRIMEURS 
WITH CHECK CHECK CONSTRAINT FK__PAPIERS_I__ID_IM__46892E07;
PRINT '✓ FK vers IMPRIMEURS réactivée';
PRINT '';

-- Vers PAPIERS
PRINT 'Réactivation FK vers PAPIERS...';
ALTER TABLE PAPIERS_IMPRIMEURS 
WITH CHECK CHECK CONSTRAINT FK__PAPIERS_I__ID_PA__459509CE;
PRINT '✓ FK vers PAPIERS réactivée';
PRINT '';

-- ============================================================================
-- ÉTAPE 2: Réactivation des Contraintes FK Entrantes
-- ============================================================================

PRINT '=== ÉTAPE 2: Réactivation des contraintes FK entrantes ===';
PRINT '';

-- Depuis PAPIERS_TARIF_FMT
PRINT 'Réactivation FK depuis PAPIERS_TARIF_FMT...';
ALTER TABLE PAPIERS_TARIF_FMT 
WITH CHECK CHECK CONSTRAINT FK__PAPIERS_T__ID_PA__49659AB2;
PRINT '✓ FK depuis PAPIERS_TARIF_FMT réactivée';
PRINT '';

-- Depuis PAPIERS_TARIF_GRAM
PRINT 'Réactivation FK depuis PAPIERS_TARIF_GRAM...';
ALTER TABLE PAPIERS_TARIF_GRAM 
WITH CHECK CHECK CONSTRAINT FK__PAPIERS_T__ID_PA__4A59BEEB;
PRINT '✓ FK depuis PAPIERS_TARIF_GRAM réactivée';
PRINT '';

-- ============================================================================
-- ÉTAPE 3: Vérification de l'État des Contraintes
-- ============================================================================

PRINT '=== ÉTAPE 3: Vérification de l''état des contraintes ===';
PRINT '';

-- Vérifier l'état des contraintes
SELECT 
    OBJECT_NAME(parent_object_id) AS Table_Name,
    name AS Constraint_Name,
    CASE 
        WHEN is_not_trusted = 0 THEN 'TRUSTED'
        ELSE 'NOT TRUSTED'
    END AS Trust_Status,
    CASE 
        WHEN is_disabled = 0 THEN 'ENABLED'
        ELSE 'DISABLED'
    END AS Status
FROM sys.foreign_keys
WHERE OBJECT_NAME(parent_object_id) IN ('PAPIERS_IMPRIMEURS', 'PAPIERS_TARIF_FMT', 'PAPIERS_TARIF_GRAM')
    AND name IN (
        'FK__PAPIERS_I__ID_IM__46892E07',
        'FK__PAPIERS_I__ID_PA__459509CE',
        'FK__PAPIERS_T__ID_PA__49659AB2',
        'FK__PAPIERS_T__ID_PA__4A59BEEB'
    )
ORDER BY Table_Name, Constraint_Name;

PRINT '';
PRINT '============================================================================';
PRINT 'REACTIVATION TERMINEE';
PRINT '============================================================================';
PRINT '';

GO
