/*
================================================================================
MISE À JOUR DU TRIGGER POUR SYNCHRONISATION DES DATES
================================================================================
Objectif : Modifier le trigger TR_WEB_GMAO_PREVENTIVE_UPDATE pour :
1. Copier automatiquement DteReal dans DateDerniereExecution quand DteReal change
2. Calculer automatiquement DateProchaineExecution = DateDerniereExecution + Periodicite

Note : Le calcul de DateProchaineExecution est également géré dans le code Python,
mais ce trigger garantit la cohérence même lors de mises à jour directes en SQL.
*/

USE novaprint_restored;
GO

-- Vérifier si les colonnes existent
IF COL_LENGTH('dbo.WEB_GMAO_PREVENTIVE', 'DateDerniereExecution') IS NULL
BEGIN
    PRINT '⚠️ La colonne DateDerniereExecution n''existe pas. Exécutez d''abord extend_web_gmao_preventive.sql'
    RETURN
END

IF COL_LENGTH('dbo.WEB_GMAO_PREVENTIVE', 'DateProchaineExecution') IS NULL
BEGIN
    PRINT '⚠️ La colonne DateProchaineExecution n''existe pas. Exécutez d''abord extend_web_gmao_preventive.sql'
    RETURN
END

GO

-- Supprimer l'ancien trigger s'il existe
IF OBJECT_ID('TR_WEB_GMAO_PREVENTIVE_UPDATE', 'TR') IS NOT NULL
BEGIN
    PRINT '📝 Suppression de l''ancien trigger TR_WEB_GMAO_PREVENTIVE_UPDATE...'
    DROP TRIGGER TR_WEB_GMAO_PREVENTIVE_UPDATE
END
GO

-- Créer le nouveau trigger avec synchronisation des dates
PRINT '📝 Création du trigger TR_WEB_GMAO_PREVENTIVE_UPDATE avec synchronisation des dates...'
GO

CREATE TRIGGER TR_WEB_GMAO_PREVENTIVE_UPDATE
ON [dbo].[WEB_GMAO_PREVENTIVE]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- 1. Mettre à jour NomPrenom_personel depuis personel si Matricule_personel a changé
    UPDATE w
    SET w.NomPrenom_personel = LTRIM(RTRIM(COALESCE(p.Nom, '') + ' ' + COALESCE(p.Prenom, ''))),
        w.DateModification = GETDATE()
    FROM [dbo].[WEB_GMAO_PREVENTIVE] w
    INNER JOIN inserted i ON w.ID = i.ID
    LEFT JOIN [dbo].[personel] p ON w.Matricule_personel = p.Matricule
    WHERE w.Matricule_personel IS NOT NULL
      AND (i.Matricule_personel != (SELECT Matricule_personel FROM deleted WHERE ID = i.ID)
           OR i.Matricule_personel IS NOT NULL);
    
    -- 2. RÈGLE 1: DateDerniereExecution doit toujours prendre la valeur de DteReal
    --    Copier DteReal dans DateDerniereExecution quand DteReal change
    UPDATE w
    SET w.DateDerniereExecution = i.DteReal,
        w.DateModification = GETDATE()
    FROM [dbo].[WEB_GMAO_PREVENTIVE] w
    INNER JOIN inserted i ON w.ID = i.ID
    INNER JOIN deleted d ON w.ID = d.ID
    WHERE i.DteReal IS NOT NULL
      AND (i.DteReal != d.DteReal OR d.DteReal IS NULL);
    
    -- 3. RÈGLE 2: DateProchaineExecution = DateDerniereExecution + Periodicite
    --    Calculer automatiquement la date prochaine exécution
    UPDATE w
    SET w.DateProchaineExecution = 
        CASE 
            -- Quotidienne: +1 jour
            WHEN i.Periodicite = 'Quotidienne' AND i.DateDerniereExecution IS NOT NULL
                THEN DATEADD(DAY, 1, i.DateDerniereExecution)
            
            -- Hebdomadaire: +7 jours
            WHEN i.Periodicite = 'Hebdomadaire' AND i.DateDerniereExecution IS NOT NULL
                THEN DATEADD(DAY, 7, i.DateDerniereExecution)
            
            -- Mensuelle: +1 mois
            WHEN i.Periodicite = 'Mensuelle' AND i.DateDerniereExecution IS NOT NULL
                THEN DATEADD(MONTH, 1, i.DateDerniereExecution)
            
            -- Trimestrielle: +3 mois
            WHEN i.Periodicite = 'Trimestrielle' AND i.DateDerniereExecution IS NOT NULL
                THEN DATEADD(MONTH, 3, i.DateDerniereExecution)
            
            -- Semestrielle: +6 mois
            WHEN i.Periodicite = 'Semestrielle' AND i.DateDerniereExecution IS NOT NULL
                THEN DATEADD(MONTH, 6, i.DateDerniereExecution)
            
            -- Annuelle: +1 an
            WHEN i.Periodicite = 'Annuelle' AND i.DateDerniereExecution IS NOT NULL
                THEN DATEADD(YEAR, 1, i.DateDerniereExecution)
            
            -- Tous les 2 ans: +2 ans
            WHEN i.Periodicite = 'Tous les 2 ans' AND i.DateDerniereExecution IS NOT NULL
                THEN DATEADD(YEAR, 2, i.DateDerniereExecution)
            
            -- Tous les 3 ans: +3 ans
            WHEN i.Periodicite = 'Tous les 3 ans' AND i.DateDerniereExecution IS NOT NULL
                THEN DATEADD(YEAR, 3, i.DateDerniereExecution)
            
            -- Tous les 5 ans: +5 ans
            WHEN i.Periodicite = 'Tous les 5 ans' AND i.DateDerniereExecution IS NOT NULL
                THEN DATEADD(YEAR, 5, i.DateDerniereExecution)
            
            -- Si la périodicité change ou DateDerniereExecution change, recalculer
            -- Sinon garder la valeur existante
            ELSE w.DateProchaineExecution
        END,
        w.DateModification = GETDATE()
    FROM [dbo].[WEB_GMAO_PREVENTIVE] w
    INNER JOIN inserted i ON w.ID = i.ID
    INNER JOIN deleted d ON w.ID = d.ID
    WHERE (i.DateDerniereExecution IS NOT NULL AND i.Periodicite IS NOT NULL)
      AND (
          -- Recalculer si DateDerniereExecution a changé
          (i.DateDerniereExecution != d.DateDerniereExecution OR d.DateDerniereExecution IS NULL)
          -- Ou si la périodicité a changé
          OR (i.Periodicite != d.Periodicite OR d.Periodicite IS NULL)
      );
END
GO

PRINT ''
PRINT '✅ Trigger TR_WEB_GMAO_PREVENTIVE_UPDATE mis à jour avec succès!'
PRINT ''
PRINT '📌 Fonctionnalités ajoutées:'
PRINT '   1. DateDerniereExecution = DteReal (copie automatique)'
PRINT '   2. DateProchaineExecution = DateDerniereExecution + Periodicite (calcul automatique)'
PRINT ''
PRINT '🔄 Périodicités supportées:'
PRINT '   - Quotidienne (+1 jour)'
PRINT '   - Hebdomadaire (+7 jours)'
PRINT '   - Mensuelle (+1 mois)'
PRINT '   - Trimestrielle (+3 mois)'
PRINT '   - Semestrielle (+6 mois)'
PRINT '   - Annuelle (+1 an)'
PRINT '   - Tous les 2 ans (+2 ans)'
PRINT '   - Tous les 3 ans (+3 ans)'
PRINT '   - Tous les 5 ans (+5 ans)'
PRINT ''
GO













