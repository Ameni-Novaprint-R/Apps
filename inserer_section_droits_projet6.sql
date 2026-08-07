/*
================================================================================
SECTIONS + DROITS PROJET 6 – sections voyage + véhicules (matricule 145)
================================================================================
*/
USE [novaprint_restored];
GO

DECLARE @ID_Proj INT;
DECLARE @CodeProj NVARCHAR(50);
DECLARE @ID_Section INT;
DECLARE @ID_Action INT;
DECLARE @nom NVARCHAR(120);

SELECT @ID_Proj = ID, @CodeProj = ISNULL(CodeProj, N'Projet 6')
FROM dbo.WEB_PROJETS WHERE NumProj = 6;

IF @ID_Proj IS NULL
BEGIN
    RAISERROR('Projet 6 introuvable dans WEB_PROJETS', 16, 1);
    RETURN;
END

UPDATE dbo.WEB_PROJETS SET Nom = N'Transport & Logistique' WHERE NumProj = 6;

DECLARE @sections TABLE (Nom NVARCHAR(120));
INSERT INTO @sections (Nom) VALUES
 (N'Nouveau voyage'),
 (N'Liste des voyages'),
 (N'Gestion des véhicules');

DECLARE c CURSOR FOR SELECT Nom FROM @sections;
OPEN c;
FETCH NEXT FROM c INTO @nom;
WHILE @@FETCH_STATUS = 0
BEGIN
    SELECT @ID_Section = ID FROM dbo.WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = @nom;
    IF @ID_Section IS NULL
    BEGIN
        INSERT INTO dbo.WEB_SECTIONS (ID_Proj, Nom, archive) VALUES (@ID_Proj, @nom, 0);
        SET @ID_Section = SCOPE_IDENTITY();
    END

    SELECT @ID_Action = ID FROM dbo.WEB_ACTIONS WHERE ID_Section = @ID_Section AND Action = N'Accès';
    IF @ID_Action IS NULL
    BEGIN
        INSERT INTO dbo.WEB_ACTIONS (ID_Section, Action, archive, CodeProj, Nom_SECTIONS)
        VALUES (@ID_Section, N'Accès', 0, @CodeProj, @nom);
        SET @ID_Action = SCOPE_IDENTITY();
    END

    IF NOT EXISTS (
        SELECT 1 FROM dbo.WEB_DROITS_ACCES WHERE Matricule = 145 AND ID_Action = @ID_Action
    )
        INSERT INTO dbo.WEB_DROITS_ACCES (Matricule, ID_Action, Autorise) VALUES (145, @ID_Action, 1);
    ELSE
        UPDATE dbo.WEB_DROITS_ACCES SET Autorise = 1 WHERE Matricule = 145 AND ID_Action = @ID_Action;

    FETCH NEXT FROM c INTO @nom;
END
CLOSE c;
DEALLOCATE c;

SELECT WS.Nom AS Section, WA.Action, WDA.Autorise
FROM dbo.WEB_DROITS_ACCES WDA
JOIN dbo.WEB_ACTIONS WA ON WA.ID = WDA.ID_Action
JOIN dbo.WEB_SECTIONS WS ON WS.ID = WA.ID_Section
JOIN dbo.WEB_PROJETS WP ON WP.ID = WS.ID_Proj
WHERE WDA.Matricule = 145 AND WP.NumProj = 6
ORDER BY WS.Nom;
GO
