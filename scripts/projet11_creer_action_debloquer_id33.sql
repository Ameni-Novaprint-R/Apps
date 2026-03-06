-- Projet 11 : action DEBLOQUER (libérer le verrou)
-- 1) WEB_ACTIONS : créer l'action avec ID=33, ID_Section=2
-- 2) WEB_DROITS_ACCES : accorder l'accès aux matricules 167, 268, 32
-- Les matricules 321 et 179 sont super-utilisateurs (accès complet sans WEB_DROITS_ACCES).

SET NOCOUNT ON;

-- 1) Créer l'action DEBLOQUER (ID=33, ID_Section=2) si elle n'existe pas
IF NOT EXISTS (SELECT 1 FROM dbo.WEB_ACTIONS WHERE ID = 33)
BEGIN
    SET IDENTITY_INSERT dbo.WEB_ACTIONS ON;

    INSERT INTO dbo.WEB_ACTIONS (ID, ID_Section, Action, archive, CodeProj, Nom_SECTIONS)
    VALUES (33, 2, 'DEBLOQUER', 0, 'Projet 11', 'Liste des Traitements');

    SET IDENTITY_INSERT dbo.WEB_ACTIONS OFF;
    PRINT 'Action DEBLOQUER créée (ID=33, ID_Section=2).';
END
ELSE
BEGIN
    -- S'assurer que la ligne existante a les bonnes valeurs
    UPDATE dbo.WEB_ACTIONS
    SET ID_Section = 2, Action = 'DEBLOQUER', archive = 0,
        CodeProj = 'Projet 11', Nom_SECTIONS = 'Liste des Traitements'
    WHERE ID = 33;
    PRINT 'Action ID=33 déjà existante, mise à jour effectuée.';
END

-- 2) Accorder l'accès (ID_Action=33) aux matricules 167, 268, 32
MERGE dbo.WEB_DROITS_ACCES AS tgt
USING (VALUES (167), (268), (32)) AS src(Matricule)
ON tgt.Matricule = src.Matricule AND tgt.ID_Action = 33
WHEN MATCHED THEN
    UPDATE SET Autorise = 1, NomAtelier = NULL
WHEN NOT MATCHED THEN
    INSERT (Matricule, NomAtelier, ID_Action, Autorise)
    VALUES (src.Matricule, NULL, 33, 1);

PRINT 'Droits DEBLOQUER (ID_Action=33) accordés aux matricules 167, 268, 32.';
PRINT 'Fin du script.';
