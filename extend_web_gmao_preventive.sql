/*
================================================================================
EXTENSION DE LA TABLE WEB_GMAO_PREVENTIVE
================================================================================
Objectif : Ajouter les colonnes nécessaires pour le planning de maintenance préventive
*/

USE novaprint_restored;
GO

-- Vérifier si les colonnes existent déjà
IF COL_LENGTH('dbo.WEB_GMAO_PREVENTIVE', 'Reference') IS NULL
BEGIN
    PRINT '📝 Ajout des colonnes au planning de maintenance préventive...'
    
    -- Référence de la tâche (ex: K1, KBA 75, etc.)
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    ADD Reference VARCHAR(50) NULL;
    
    -- Description de la tâche
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    ADD Tache NVARCHAR(500) NULL;
    
    -- Périodicité (Quotidienne, Hebdomadaire, Mensuelle, Trimestrielle, Semestrielle, Annuelle)
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    ADD Periodicite VARCHAR(50) NULL CHECK (Periodicite IN ('Quotidienne', 'Hebdomadaire', 'Mensuelle', 'Trimestrielle', 'Semestrielle', 'Annuelle'));
    
    -- Durée estimée (ex: 5 min, 10 min, 1h, 2h, 8h)
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    ADD Duree VARCHAR(20) NULL;
    
    -- Rôle requis (Opérateur, Technicien, Mécanicien, Électricien, Chef d''équipe)
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    ADD RoleRequis VARCHAR(50) NULL;
    
    -- Spécifications et observations
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    ADD SpecificationsObservations NTEXT NULL;
    
    -- Ordre d'affichage dans le planning
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    ADD OrdreAffichage INT NULL;
    
    -- Date de dernière exécution (pour le suivi)
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    ADD DateDerniereExecution DATETIME NULL;
    
    -- Date de prochaine exécution prévue (calculée selon la périodicité)
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    ADD DateProchaineExecution DATETIME NULL;
    
    PRINT '✅ Colonnes ajoutées avec succès!'
END
ELSE
BEGIN
    PRINT '⚠️ Les colonnes existent déjà.'
END
GO

-- Créer des index supplémentaires pour améliorer les performances
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_WEB_GMAO_PREVENTIVE_Periodicite')
BEGIN
    CREATE NONCLUSTERED INDEX IX_WEB_GMAO_PREVENTIVE_Periodicite 
    ON dbo.WEB_GMAO_PREVENTIVE(Periodicite);
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_WEB_GMAO_PREVENTIVE_Reference')
BEGIN
    CREATE NONCLUSTERED INDEX IX_WEB_GMAO_PREVENTIVE_Reference 
    ON dbo.WEB_GMAO_PREVENTIVE(Reference);
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_WEB_GMAO_PREVENTIVE_Nom_GP_POSTES_Periodicite')
BEGIN
    CREATE NONCLUSTERED INDEX IX_WEB_GMAO_PREVENTIVE_Nom_GP_POSTES_Periodicite 
    ON dbo.WEB_GMAO_PREVENTIVE(Nom_GP_POSTES, Periodicite);
END
GO

PRINT ''
PRINT '✅ Extension de la table WEB_GMAO_PREVENTIVE terminée!'
PRINT ''
PRINT '📌 Nouvelles colonnes ajoutées:'
PRINT '   - Reference : Référence de la tâche (ex: K1, KBA 75)'
PRINT '   - Tache : Description de la tâche'
PRINT '   - Periodicite : Fréquence (Quotidienne, Hebdomadaire, etc.)'
PRINT '   - Duree : Durée estimée (ex: 5 min, 1h)'
PRINT '   - RoleRequis : Rôle requis (Opérateur, Technicien, etc.)'
PRINT '   - SpecificationsObservations : Notes et observations'
PRINT '   - OrdreAffichage : Ordre d''affichage dans le planning'
PRINT '   - DateDerniereExecution : Date de dernière exécution'
PRINT '   - DateProchaineExecution : Date de prochaine exécution prévue'
GO

















