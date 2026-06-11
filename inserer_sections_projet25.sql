/*
================================================================================
INSERTION DES SECTIONS DU PROJET 25 DANS WEB_SECTIONS
================================================================================
*/
USE [novaprint_restored];
GO

DECLARE @ID_Proj INT;
SELECT @ID_Proj = ID FROM dbo.WEB_PROJETS WHERE NumProj = 25;
IF @ID_Proj IS NULL
BEGIN
    INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive)
    VALUES (25, 'Projet 25', N'Gestion des congés et autorisations de sortie', 0);
    SELECT @ID_Proj = SCOPE_IDENTITY();
END

DECLARE @sections TABLE (Nom NVARCHAR(120));
INSERT INTO @sections (Nom) VALUES
 (N'Demande de congé'),
 (N'Demande d''autorisation de sortie'),
 (N'Mes demandes'),
 (N'Demandes à valider'),
 (N'Vue RH'),
 (N'Statistiques'),
 (N'Organigramme validateurs'),
 (N'Jours fériés'),
 (N'Solde de congés');

DECLARE @nom NVARCHAR(120);
DECLARE c CURSOR FOR SELECT Nom FROM @sections;
OPEN c;
FETCH NEXT FROM c INTO @nom;
WHILE @@FETCH_STATUS = 0
BEGIN
    INSERT INTO dbo.WEB_SECTIONS (ID_Proj, Nom, archive)
    SELECT @ID_Proj, @nom, 0
    WHERE NOT EXISTS (SELECT 1 FROM dbo.WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = @nom);
    FETCH NEXT FROM c INTO @nom;
END
CLOSE c;
DEALLOCATE c;

SELECT s.ID, s.Nom FROM dbo.WEB_SECTIONS s WHERE s.ID_Proj = @ID_Proj ORDER BY s.ID;
GO
