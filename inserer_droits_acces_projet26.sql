/*
================================================================================
DROITS D'ACCÈS PROJET 26 – Demande + Évaluation pour tous les employés actifs
================================================================================
Exécuter après inserer_sections_projet26.sql
*/
USE [novaprint_restored];
GO

DECLARE @ID_Proj INT;
SELECT @ID_Proj = ID FROM dbo.WEB_PROJETS WHERE NumProj = 26;
IF @ID_Proj IS NULL
BEGIN
    RAISERROR('Projet 26 introuvable dans WEB_PROJETS', 16, 1);
    RETURN;
END

DECLARE @CodeProj NVARCHAR(50);
SELECT @CodeProj = ISNULL(CodeProj, N'Projet 26') FROM dbo.WEB_PROJETS WHERE ID = @ID_Proj;

DECLARE @sections TABLE (Nom NVARCHAR(120));
INSERT INTO @sections (Nom) VALUES
 (N'Demande de formation'),
 (N'Évaluation de formation');

DECLARE @nom NVARCHAR(120);
DECLARE @ID_Section INT;
DECLARE @ID_Action INT;

DECLARE c CURSOR FOR SELECT Nom FROM @sections;
OPEN c;
FETCH NEXT FROM c INTO @nom;
WHILE @@FETCH_STATUS = 0
BEGIN
    SELECT @ID_Section = ID FROM dbo.WEB_SECTIONS WHERE ID_Proj = @ID_Proj AND Nom = @nom;
    IF @ID_Section IS NOT NULL
    BEGIN
        SELECT @ID_Action = ID FROM dbo.WEB_ACTIONS WHERE ID_Section = @ID_Section AND Action = N'Accès';
        IF @ID_Action IS NULL
        BEGIN
            INSERT INTO dbo.WEB_ACTIONS (ID_Section, Action, archive, CodeProj, Nom_SECTIONS)
            VALUES (@ID_Section, N'Accès', 0, @CodeProj, @nom);
            SET @ID_Action = SCOPE_IDENTITY();
        END

        INSERT INTO dbo.WEB_DROITS_ACCES (Matricule, ID_Action, Autorise)
        SELECT p.Matricule, @ID_Action, 1
        FROM dbo.personel p
        WHERE (p.archive = 0 OR p.archive IS NULL)
          AND NOT EXISTS (
              SELECT 1 FROM dbo.WEB_DROITS_ACCES d
              WHERE d.Matricule = p.Matricule AND d.ID_Action = @ID_Action
          );
    END
    FETCH NEXT FROM c INTO @nom;
END
CLOSE c;
DEALLOCATE c;

SELECT COUNT(*) AS nb_droits_demande_eval
FROM dbo.WEB_DROITS_ACCES d
INNER JOIN dbo.WEB_ACTIONS a ON a.ID = d.ID_Action
INNER JOIN dbo.WEB_SECTIONS s ON s.ID = a.ID_Section
WHERE s.ID_Proj = @ID_Proj
  AND s.Nom IN (N'Demande de formation', N'Évaluation de formation')
  AND a.Action = N'Accès';
GO
