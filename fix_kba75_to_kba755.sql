/*
================================================================================
CORRECTION DE LA COLONNE Nom_GP_POSTES DANS WEB_GMAO_PREVENTIVE
================================================================================
Objectif : Remplacer "KBA 75" par "KBA755" dans la colonne Nom_GP_POSTES
*/

USE novaprint_restored;
GO

-- Afficher les lignes concernées avant la mise à jour
PRINT '📊 Lignes concernées avant la mise à jour:'
SELECT COUNT(*) as NombreLignes
FROM dbo.WEB_GMAO_PREVENTIVE
WHERE Nom_GP_POSTES = 'KBA 75';
GO

-- Effectuer la mise à jour
PRINT '📝 Mise à jour en cours...'
UPDATE dbo.WEB_GMAO_PREVENTIVE
SET Nom_GP_POSTES = 'KBA755'
WHERE Nom_GP_POSTES = 'KBA 75';
GO

-- Afficher le nombre de lignes mises à jour
DECLARE @RowsAffected INT;
SET @RowsAffected = @@ROWCOUNT;
PRINT '';
PRINT CONCAT('✅ ', @RowsAffected, ' ligne(s) mise(s) à jour avec succès!');
GO

-- Vérifier qu'il ne reste plus de "KBA 75"
PRINT '';
PRINT '🔍 Vérification...'
SELECT COUNT(*) as NombreRestant
FROM dbo.WEB_GMAO_PREVENTIVE
WHERE Nom_GP_POSTES = 'KBA 75';
GO

-- Afficher un échantillon des lignes mises à jour
PRINT '';
PRINT '📋 Échantillon des lignes mises à jour:'
SELECT TOP 10 
    ID,
    Nom_GP_POSTES,
    Reference,
    Tache
FROM dbo.WEB_GMAO_PREVENTIVE
WHERE Nom_GP_POSTES = 'KBA755';
GO

PRINT '';
PRINT '✅ Correction terminée!'
GO














