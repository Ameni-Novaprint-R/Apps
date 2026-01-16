/*
================================================================================
AJOUT DE LA COLONNE TypeIN DANS WEB_GMAO_REPARATION
================================================================================
Objectif : tracer la provenance d'une fiche
- 'R' : fiche issue d'une réparation classique
- 'P' : fiche issue d'une intervention préventive
*/

USE novaprint_restored;
GO

IF COL_LENGTH('dbo.WEB_GMAO_REPARATION', 'TypeIN') IS NULL
BEGIN
    PRINT '📝 Ajout de la colonne TypeIN...';
    ALTER TABLE dbo.WEB_GMAO_REPARATION
    ADD TypeIN CHAR(1) NULL CONSTRAINT CK_WEB_GMAO_REPARATION_TypeIN CHECK (TypeIN IN ('R','P')) CONSTRAINT DF_WEB_GMAO_REPARATION_TypeIN DEFAULT 'R';
    
    PRINT '🔄 Mise à jour des lignes existantes avec la valeur par défaut R...';
    UPDATE dbo.WEB_GMAO_REPARATION SET TypeIN = 'R' WHERE TypeIN IS NULL;
    
    PRINT '✅ Colonne TypeIN ajoutée et initialisée.';
END
ELSE
BEGIN
    PRINT 'ℹ️ La colonne TypeIN existe déjà. Aucune action nécessaire.';
END














