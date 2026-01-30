-- ================================================================================
-- AJOUT DES COLONNES CodeProj ET Nom_SECTIONS À LA TABLE WEB_ACTIONS
-- Base de données: novaprint_restored
-- Date: 29 Janvier 2026
-- ================================================================================
-- 
-- Ce script ajoute deux colonnes à WEB_ACTIONS :
-- 1. CodeProj : affiche la valeur de CodeProj de WEB_PROJETS (via WEB_SECTIONS)
-- 2. Nom_SECTIONS : affiche la valeur de Nom de WEB_SECTIONS
--
-- Relations :
-- WEB_ACTIONS.ID_Section -> WEB_SECTIONS.ID -> WEB_SECTIONS.ID_Proj -> WEB_PROJETS.ID -> WEB_PROJETS.CodeProj
-- WEB_ACTIONS.ID_Section -> WEB_SECTIONS.ID -> WEB_SECTIONS.Nom
-- ================================================================================

USE novaprint_restored;
GO

PRINT '================================================================================';
PRINT 'AJOUT DES COLONNES CodeProj ET Nom_SECTIONS À WEB_ACTIONS';
PRINT '================================================================================';
PRINT '';

-- Vérifier que la table existe (peut être WEB_ACTIONS ou WEB_DROITS_ACCES)
DECLARE @TableName NVARCHAR(128);
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_ACTIONS')
    SET @TableName = 'WEB_ACTIONS';
ELSE IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_DROITS_ACCES')
    SET @TableName = 'WEB_DROITS_ACCES';
ELSE
BEGIN
    PRINT 'ERREUR: Ni WEB_ACTIONS ni WEB_DROITS_ACCES n''existent.';
    PRINT 'Arrêt du script.';
    RETURN;
END

PRINT 'Table trouvée: ' + @TableName;
PRINT '';

-- ================================================================================
-- ÉTAPE 1: Ajouter la colonne CodeProj
-- ================================================================================
PRINT '[1/2] Ajout de la colonne CodeProj...';

IF EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = @TableName AND COLUMN_NAME = 'CodeProj'
)
BEGIN
    PRINT '  ⚠ La colonne CodeProj existe déjà.';
END
ELSE
BEGIN
    EXEC('ALTER TABLE dbo.' + @TableName + ' ADD CodeProj NVARCHAR(50) NULL');
    PRINT '  ✓ Colonne CodeProj ajoutée.';
END
PRINT '';

-- ================================================================================
-- ÉTAPE 2: Ajouter la colonne Nom_SECTIONS
-- ================================================================================
PRINT '[2/2] Ajout de la colonne Nom_SECTIONS...';

IF EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = @TableName AND COLUMN_NAME = 'Nom_SECTIONS'
)
BEGIN
    PRINT '  ⚠ La colonne Nom_SECTIONS existe déjà.';
END
ELSE
BEGIN
    EXEC('ALTER TABLE dbo.' + @TableName + ' ADD Nom_SECTIONS NVARCHAR(200) NULL');
    PRINT '  ✓ Colonne Nom_SECTIONS ajoutée.';
END
PRINT '';

-- ================================================================================
-- ÉTAPE 3: Mettre à jour les valeurs existantes
-- ================================================================================
PRINT '[3/3] Mise à jour des valeurs existantes...';

-- Mettre à jour CodeProj et Nom_SECTIONS pour toutes les lignes existantes
EXEC('
    UPDATE dbo.' + @TableName + '
    SET 
        CodeProj = (
            SELECT p.CodeProj
            FROM dbo.WEB_SECTIONS s
            INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
            WHERE s.ID = ' + @TableName + '.ID_Section
        ),
        Nom_SECTIONS = (
            SELECT s.Nom
            FROM dbo.WEB_SECTIONS s
            WHERE s.ID = ' + @TableName + '.ID_Section
        )
    WHERE ID_Section IS NOT NULL
');

DECLARE @RowCount INT;
EXEC('SELECT @RowCount = COUNT(*) FROM dbo.' + @TableName + ' WHERE CodeProj IS NOT NULL OR Nom_SECTIONS IS NOT NULL');
PRINT '  ✓ ' + CAST(@RowCount AS NVARCHAR(10)) + ' ligne(s) mise(s) à jour.';
PRINT '';

-- ================================================================================
-- ÉTAPE 4: Créer un trigger pour maintenir la synchronisation
-- ================================================================================
PRINT '[4/4] Création du trigger de synchronisation...';

-- Supprimer le trigger s'il existe déjà
IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'TRG_WEB_ACTIONS_UPDATE_CODE_NOM')
BEGIN
    EXEC('DROP TRIGGER TRG_WEB_ACTIONS_UPDATE_CODE_NOM');
    PRINT '  ⚠ Ancien trigger supprimé.';
END

-- Créer le trigger pour maintenir CodeProj et Nom_SECTIONS à jour
EXEC('
    CREATE TRIGGER TRG_WEB_ACTIONS_UPDATE_CODE_NOM
    ON dbo.' + @TableName + '
    AFTER INSERT, UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        
        -- Mettre à jour CodeProj et Nom_SECTIONS pour les lignes insérées ou modifiées
        UPDATE wa
        SET 
            CodeProj = (
                SELECT p.CodeProj
                FROM dbo.WEB_SECTIONS s
                INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
                WHERE s.ID = wa.ID_Section
            ),
            Nom_SECTIONS = (
                SELECT s.Nom
                FROM dbo.WEB_SECTIONS s
                WHERE s.ID = wa.ID_Section
            )
        FROM dbo.' + @TableName + ' wa
        INNER JOIN inserted i ON i.ID = wa.ID
        WHERE wa.ID_Section IS NOT NULL;
    END
');

PRINT '  ✓ Trigger TRG_WEB_ACTIONS_UPDATE_CODE_NOM créé.';
PRINT '';

-- ================================================================================
-- VÉRIFICATION
-- ================================================================================
PRINT '================================================================================';
PRINT 'VÉRIFICATION';
PRINT '================================================================================';
PRINT '';

-- Afficher la structure de la table
PRINT 'Structure de la table ' + @TableName + ':';
EXEC('
    SELECT 
        COLUMN_NAME AS Colonne,
        DATA_TYPE AS Type,
        CASE 
            WHEN CHARACTER_MAXIMUM_LENGTH IS NOT NULL 
            THEN CAST(DATA_TYPE AS VARCHAR) + ''('' + CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR) + '')''
            ELSE DATA_TYPE
        END AS Type_Complet,
        IS_NULLABLE AS Nullable
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = ''' + @TableName + '''
    ORDER BY ORDINAL_POSITION
');

PRINT '';
PRINT 'Exemple de données avec les nouvelles colonnes:';
EXEC('
    SELECT TOP 5
        wa.ID,
        wa.ID_Section,
        wa.CodeProj,
        wa.Nom_SECTIONS,
        wa.Action,
        wa.archive
    FROM dbo.' + @TableName + ' wa
    ORDER BY wa.ID
');

PRINT '';
PRINT '================================================================================';
PRINT 'MODIFICATIONS TERMINÉES';
PRINT '================================================================================';
PRINT '';
PRINT 'Les colonnes CodeProj et Nom_SECTIONS ont été ajoutées et remplies.';
PRINT 'Un trigger a été créé pour maintenir ces valeurs à jour automatiquement.';
PRINT '';

GO
