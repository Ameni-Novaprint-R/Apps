/*
================================================================================
INSERTION DES SECTIONS DU PROJET 11 DANS WEB_SECTIONS
================================================================================
Base de données : novaprint_restored
Projet 11 = Gestion des Traitements (ID=11 dans WEB_PROJETS).

Sections à ajouter :
- Nouvelle fiche de production
- Liste des Traitements
- Statistiques

Chaque INSERT est conditionnel : pas d'erreur si la section existe déjà
(UNIQUE ID_Proj, Nom).
================================================================================
*/

USE [novaprint_restored]
GO

PRINT 'Insertion des sections du Projet 11 dans WEB_SECTIONS...'
PRINT ''

-- ID_Proj = 11 (Projet 11 dans WEB_PROJETS, ID=NumProj)
DECLARE @ID_Proj INT = 11;

-- Nouvelle fiche de production
INSERT INTO dbo.WEB_SECTIONS (ID_Proj, Nom, archive)
SELECT @ID_Proj, N'Nouvelle fiche de production', 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = N'Nouvelle fiche de production');
PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  + Nouvelle fiche de production' ELSE '  (déjà présente) Nouvelle fiche de production' END;

-- Liste des Traitements
INSERT INTO dbo.WEB_SECTIONS (ID_Proj, Nom, archive)
SELECT @ID_Proj, N'Liste des Traitements', 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = N'Liste des Traitements');
PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  + Liste des Traitements' ELSE '  (déjà présente) Liste des Traitements' END;

-- Statistiques
INSERT INTO dbo.WEB_SECTIONS (ID_Proj, Nom, archive)
SELECT @ID_Proj, N'Statistiques', 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = N'Statistiques');
PRINT CASE WHEN @@ROWCOUNT > 0 THEN '  + Statistiques' ELSE '  (déjà présente) Statistiques' END;

PRINT ''
PRINT 'Sections du Projet 11 :'
SELECT s.ID, s.ID_Proj, p.NumProj, p.CodeProj, s.Nom, s.archive
FROM dbo.WEB_SECTIONS s
INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
WHERE s.ID_Proj = @ID_Proj
ORDER BY s.ID;

PRINT ''
PRINT 'Fin du script.'
GO
