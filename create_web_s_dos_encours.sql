-- Script de création de la table WEB_S_DOS_ENCOURS
-- Base de données: NOVAPRINT_restored

-- Supprimer la table si elle existe déjà
IF OBJECT_ID('WEB_S_DOS_ENCOURS', 'U') IS NOT NULL
    DROP TABLE WEB_S_DOS_ENCOURS;
GO

-- Créer la table WEB_S_DOS_ENCOURS
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
GO

-- Créer un index sur Numero_COMMANDES pour améliorer les performances de recherche
CREATE INDEX IX_WEB_S_DOS_ENCOURS_Numero ON WEB_S_DOS_ENCOURS(Numero_COMMANDES);
GO

-- Copier les données initiales depuis COMMANDES et SOCIETES
INSERT INTO WEB_S_DOS_ENCOURS (
    Numero_COMMANDES,
    RaiSocTri_SOCIETES,
    Reference_COMMANDES,
    QteComm_COMMANDES,
    Coef_COMMANDES
)
SELECT 
    C.Numero AS Numero_COMMANDES,
    S.RaiSocTri AS RaiSocTri_SOCIETES,
    C.Reference AS Reference_COMMANDES,
    C.QteComm AS QteComm_COMMANDES,
    C.Coef AS Coef_COMMANDES
FROM 
    COMMANDES C
    LEFT JOIN SOCIETES S ON C.ID_SOCIETE = S.ID;
GO

-- Afficher le nombre de lignes insérées
SELECT COUNT(*) AS NombreLignesInserees FROM WEB_S_DOS_ENCOURS;
GO




