-- Ajouter la colonne Description à WEB_TRAITEMENTS (texte libre pour la fiche de production)
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'WEB_TRAITEMENTS' AND COLUMN_NAME = 'Description'
)
BEGIN
    ALTER TABLE dbo.WEB_TRAITEMENTS ADD Description NVARCHAR(MAX) NULL;
    PRINT 'Colonne Description ajoutée à WEB_TRAITEMENTS.';
END
ELSE
    PRINT 'Colonne Description existe déjà.';
