USE novaprint_restored;
GO

IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS'
      AND COLUMN_NAME = 'DateInventaire'
)
BEGIN
    ALTER TABLE WEB_S_DOS_ENCOURS
    ADD DateInventaire DATE NULL;

    PRINT 'Colonne DateInventaire ajoutee dans WEB_S_DOS_ENCOURS.';
END
ELSE
BEGIN
    PRINT 'La colonne DateInventaire existe deja dans WEB_S_DOS_ENCOURS.';
END
GO
