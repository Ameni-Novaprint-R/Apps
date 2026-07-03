/*
================================================================================
INSERTION DES SECTIONS DU PROJET 27 DANS WEB_SECTIONS
================================================================================
*/
USE [novaprint_restored];
GO

DECLARE @ID_Proj INT;
SELECT @ID_Proj = ID FROM dbo.WEB_PROJETS WHERE NumProj = 27;
IF @ID_Proj IS NULL
BEGIN
    INSERT INTO dbo.WEB_PROJETS (NumProj, CodeProj, Nom, archive)
    VALUES (27, N'Projet 27', N'Crédit Leasing', 0);
    SELECT @ID_Proj = SCOPE_IDENTITY();
END

DECLARE @sections TABLE (Nom NVARCHAR(120));
INSERT INTO @sections (Nom) VALUES
 (N'Tableau de bord'),
 (N'Gestion des crédits'),
 (N'Nouveau crédit');

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
