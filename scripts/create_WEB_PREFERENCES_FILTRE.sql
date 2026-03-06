-- Table pour enregistrer les filtres par utilisateur (matricule)
-- Exécuter ce script si la table n'existe pas
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'WEB_PREFERENCES_FILTRE')
BEGIN
    CREATE TABLE dbo.WEB_PREFERENCES_FILTRE (
        Matricule INT NOT NULL,
        Cle NVARCHAR(50) NOT NULL,
        Valeur NVARCHAR(MAX),
        PRIMARY KEY (Matricule, Cle)
    );
    PRINT 'Table WEB_PREFERENCES_FILTRE créée.';
END
ELSE
    PRINT 'Table WEB_PREFERENCES_FILTRE existe déjà.';
