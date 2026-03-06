-- ============================================================================
-- Script : Vider les fiches de demande d'intervention et fiches de réparation GMAO
--          et réinitialiser les ID à partir de 1
-- ============================================================================
-- ATTENTION : Ce script supprime DÉFINITIVEMENT toutes les données des deux
-- listes. À exécuter uniquement pour repartir à zéro (fin des données de test).
-- ============================================================================

BEGIN TRANSACTION;

-- 1. Supprimer les articles associés (table enfant avec clés étrangères)
DELETE FROM dbo.WEB_GMAO_ARTICLES;

-- 2. Supprimer toutes les fiches de réparation
DELETE FROM dbo.WEB_GMAO_REPARATION;

-- 3. Supprimer toutes les fiches de demande d'intervention
DELETE FROM dbo.WEB_GMAO;

-- 4. Réinitialiser l'IDENTITY pour que les prochains ID commencent à 1
DBCC CHECKIDENT ('dbo.WEB_GMAO', RESEED, 0);
DBCC CHECKIDENT ('dbo.WEB_GMAO_REPARATION', RESEED, 0);

-- Vérification : les tables doivent être vides
SELECT 'WEB_GMAO' AS TableName, COUNT(*) AS NbLignes FROM dbo.WEB_GMAO
UNION ALL
SELECT 'WEB_GMAO_REPARATION', COUNT(*) FROM dbo.WEB_GMAO_REPARATION
UNION ALL
SELECT 'WEB_GMAO_ARTICLES', COUNT(*) FROM dbo.WEB_GMAO_ARTICLES;

COMMIT TRANSACTION;

PRINT 'Vidage terminé : les deux listes sont vides et les ID repartiront à 1.';
