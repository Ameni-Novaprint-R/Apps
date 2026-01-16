/*
================================================================================
AJOUT DE LA CONTRAINTE CHECK POUR ID_StatRep
================================================================================
Objectif : Garantir que si ID_WEB_GMAO_Dem_In est NULL, alors ID_StatRep doit être NULL
Règle : ID_StatRep ne peut avoir une valeur que si ID_WEB_GMAO_Dem_In n'est pas NULL
*/

USE novaprint_restored;
GO

-- Vérifier si la contrainte existe déjà
IF EXISTS (
    SELECT 1 
    FROM sys.check_constraints 
    WHERE name = 'CK_WEB_GMAO_REPARATION_StatRep_When_DemIn_Null'
)
BEGIN
    PRINT '⚠️ La contrainte existe déjà. Suppression de l''ancienne contrainte...'
    ALTER TABLE dbo.WEB_GMAO_REPARATION
    DROP CONSTRAINT CK_WEB_GMAO_REPARATION_StatRep_When_DemIn_Null;
END
GO

-- Nettoyer les données existantes qui violent la règle
-- Si ID_WEB_GMAO_Dem_In est NULL, mettre ID_StatRep à NULL
PRINT '📝 Nettoyage des données existantes...'
UPDATE dbo.WEB_GMAO_REPARATION
SET ID_StatRep = NULL
WHERE ID_WEB_GMAO_Dem_In IS NULL AND ID_StatRep IS NOT NULL;
GO

PRINT '✅ Données nettoyées!'
PRINT ''

-- Ajouter la contrainte CHECK
PRINT '📝 Ajout de la contrainte CHECK...'
ALTER TABLE dbo.WEB_GMAO_REPARATION
ADD CONSTRAINT CK_WEB_GMAO_REPARATION_StatRep_When_DemIn_Null
CHECK (ID_WEB_GMAO_Dem_In IS NOT NULL OR ID_StatRep IS NULL);
GO

PRINT '✅ Contrainte ajoutée avec succès!'
PRINT ''
PRINT '📌 Règle appliquée:'
PRINT '   - Si ID_WEB_GMAO_Dem_In est NULL, alors ID_StatRep doit être NULL'
PRINT '   - ID_StatRep ne peut avoir une valeur que si ID_WEB_GMAO_Dem_In n''est pas NULL'
GO














