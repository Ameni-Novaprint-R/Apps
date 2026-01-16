-- Script SQL pour verifier et creer la table WEB_S_DOS_ENCOURS
-- A executer directement sur le serveur SQL Server 192.168.10.225
-- Base de donnees: novaprint_restored

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
        COLUMN_NAME,
        DATA_TYPE,
        CHARACTER_MAXIMUM_LENGTH,
        IS_NULLABLE,
        COLUMN_DEFAULT
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
    
    -- Creer l'index
    CREATE INDEX IX_WEB_S_DOS_ENCOURS_Numero 
    ON WEB_S_DOS_ENCOURS(Numero_COMMANDES);
    
    PRINT 'Table WEB_S_DOS_ENCOURS creee avec succes!';
END
GO

-- Verifier le serveur
SELECT 
    @@SERVERNAME AS ServerName,
    DB_NAME() AS DatabaseName,
    HOST_NAME() AS HostName;
GO

