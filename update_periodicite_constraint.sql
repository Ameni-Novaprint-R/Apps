/*
================================================================================
MISE À JOUR DE LA CONTRAINTE CHECK POUR PERIODICITE
================================================================================
Ajoute les nouvelles périodicités : Tous les 2 ans, Tous les 3 ans, Tous les 5 ans
*/

USE novaprint_restored;
GO

-- Supprimer l'ancienne contrainte
IF EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK__WEB_GMAO___Perio__5912BDED')
BEGIN
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    DROP CONSTRAINT CK__WEB_GMAO___Perio__5912BDED;
    PRINT '✅ Ancienne contrainte supprimée';
END
GO

-- Supprimer la contrainte par nom si elle existe avec un autre nom
DECLARE @constraint_name NVARCHAR(200);
SELECT @constraint_name = name 
FROM sys.check_constraints 
WHERE parent_object_id = OBJECT_ID('WEB_GMAO_PREVENTIVE') 
  AND definition LIKE '%Periodicite%';

IF @constraint_name IS NOT NULL
BEGIN
    EXEC('ALTER TABLE dbo.WEB_GMAO_PREVENTIVE DROP CONSTRAINT ' + @constraint_name);
    PRINT '✅ Contrainte existante supprimée: ' + @constraint_name;
END
GO

-- Créer la nouvelle contrainte avec toutes les périodicités
ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
ADD CONSTRAINT CK_WEB_GMAO_PREVENTIVE_Periodicite 
CHECK (Periodicite IN (
    'Quotidienne', 
    'Hebdomadaire', 
    'Mensuelle', 
    'Trimestrielle', 
    'Semestrielle', 
    'Annuelle',
    'Tous les 2 ans',
    'Tous les 3 ans',
    'Tous les 5 ans'
) OR Periodicite IS NULL);
GO

PRINT '✅ Nouvelle contrainte créée avec succès';
PRINT '';
PRINT '📌 Périodicités acceptées:';
PRINT '   - Quotidienne';
PRINT '   - Hebdomadaire';
PRINT '   - Mensuelle';
PRINT '   - Trimestrielle';
PRINT '   - Semestrielle';
PRINT '   - Annuelle';
PRINT '   - Tous les 2 ans';
PRINT '   - Tous les 3 ans';
PRINT '   - Tous les 5 ans';
GO

















