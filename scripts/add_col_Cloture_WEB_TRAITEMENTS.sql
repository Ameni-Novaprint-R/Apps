-- Ajouter la colonne Cloture à WEB_TRAITEMENTS
-- 1 = fiche clôturée (étape terminée), 0 ou NULL = non clôturée
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'WEB_TRAITEMENTS' AND COLUMN_NAME = 'Cloture'
)
BEGIN
    ALTER TABLE dbo.WEB_TRAITEMENTS ADD Cloture TINYINT NULL DEFAULT 0;
    PRINT 'Colonne Cloture ajoutée à WEB_TRAITEMENTS.';
END
ELSE
    PRINT 'Colonne Cloture existe déjà.';
