/*
Ajout de la colonne DteReal si elle n'existe pas
*/
USE novaprint_restored;
GO

IF COL_LENGTH('dbo.WEB_GMAO_PREVENTIVE', 'DteReal') IS NULL
BEGIN
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    ADD DteReal DATETIME NULL;
    PRINT 'Colonne DteReal ajoutee avec succes'
END
ELSE
BEGIN
    PRINT 'La colonne DteReal existe deja'
END
GO

IF COL_LENGTH('dbo.WEB_GMAO_PREVENTIVE', 'DtePrev') IS NULL
BEGIN
    ALTER TABLE dbo.WEB_GMAO_PREVENTIVE
    ADD DtePrev DATETIME NULL;
    PRINT 'Colonne DtePrev ajoutee avec succes'
END
ELSE
BEGIN
    PRINT 'La colonne DtePrev existe deja'
END
GO













