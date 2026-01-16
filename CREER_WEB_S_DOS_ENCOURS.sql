-- ============================================================================
-- SCRIPT DE CREATION IMMEDIATE DE LA TABLE WEB_S_DOS_ENCOURS
-- ============================================================================
-- A EXECUTER DIRECTEMENT SUR LE SERVEUR SQL SERVER 192.168.10.225
-- Base de donnees: novaprint_restored
-- ============================================================================

USE novaprint_restored;
GO

-- Verifier si la table existe
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS')
BEGIN
    PRINT 'La table WEB_S_DOS_ENCOURS existe deja.';
    
    -- Afficher le nombre de lignes
    DECLARE @count INT;
    SELECT @count = COUNT(*) FROM WEB_S_DOS_ENCOURS;
    PRINT 'Nombre de lignes: ' + CAST(@count AS VARCHAR(10));
    
    -- Afficher la structure
    SELECT 
        COLUMN_NAME AS 'Colonne',
        DATA_TYPE + 
        CASE 
            WHEN CHARACTER_MAXIMUM_LENGTH IS NOT NULL 
            THEN '(' + CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR) + ')'
            ELSE ''
        END AS 'Type',
        IS_NULLABLE AS 'Nullable',
        COLUMN_DEFAULT AS 'Valeur par defaut'
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS'
    ORDER BY ORDINAL_POSITION;
END
ELSE
BEGIN
    PRINT 'Creation de la table WEB_S_DOS_ENCOURS...';
    
    -- Creer la table
    CREATE TABLE WEB_S_DOS_ENCOURS (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        Numero_COMMANDES NVARCHAR(255) NULL,
        RaiSocTri_SOCIETES NVARCHAR(255) NULL,
        Reference_COMMANDES NVARCHAR(255) NULL,
        QteComm_COMMANDES INT NULL,
        Coef_COMMANDES DECIMAL(18,2) NULL,
        DateCreation DATETIME DEFAULT GETDATE(),
        DateModification DATETIME DEFAULT GETDATE()
    );
    
    PRINT 'Table WEB_S_DOS_ENCOURS creee avec succes!';
    
    -- Creer l'index
    CREATE INDEX IX_WEB_S_DOS_ENCOURS_Numero 
    ON WEB_S_DOS_ENCOURS(Numero_COMMANDES);
    
    PRINT 'Index IX_WEB_S_DOS_ENCOURS_Numero cree avec succes!';
    
    -- Verifier
    DECLARE @count_new INT;
    SELECT @count_new = COUNT(*) FROM WEB_S_DOS_ENCOURS;
    PRINT 'Table creee avec ' + CAST(@count_new AS VARCHAR(10)) + ' lignes (vide par defaut).';
END
GO

-- Afficher les informations du serveur pour verification
SELECT 
    @@SERVERNAME AS 'Serveur SQL',
    DB_NAME() AS 'Base de donnees',
    HOST_NAME() AS 'Machine hote';
GO

PRINT '';
PRINT '============================================================================';
PRINT 'VERIFICATION TERMINEE';
PRINT 'La table WEB_S_DOS_ENCOURS est sur le serveur reseau 192.168.10.225';
PRINT '============================================================================';
GO




