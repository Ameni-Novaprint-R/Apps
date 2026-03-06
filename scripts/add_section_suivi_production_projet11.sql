-- Ajouter la section "Suivi Production" au Projet 11
-- À exécuter si vous utilisez les droits par section (WEB_DROITS_ACCES)
-- et souhaitez contrôler l'accès à la section Suivi Production

-- 1. Insérer la section (si elle n'existe pas)
IF NOT EXISTS (SELECT 1 FROM dbo.WEB_SECTIONS ws 
               INNER JOIN dbo.WEB_PROJETS wp ON wp.ID = ws.ID_Proj 
               WHERE wp.NumProj = 11 AND ws.Nom = 'Suivi Production')
BEGIN
    INSERT INTO dbo.WEB_SECTIONS (ID_Proj, Nom)
    SELECT wp.ID, 'Suivi Production'
    FROM dbo.WEB_PROJETS wp
    WHERE wp.NumProj = 11;
    PRINT 'Section "Suivi Production" ajoutée.';
END
ELSE
    PRINT 'Section "Suivi Production" existe déjà.';
