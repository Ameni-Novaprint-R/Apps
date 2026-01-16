/*
================================================================================
CRÉATION DE LA TABLE WEB_GMAO_REPARATION
================================================================================
Objectif : Créer une table dédiée aux informations de réparation
et migrer les données depuis WEB_GMAO
*/

USE novaprint_restored;
GO

-- Vérifier si la table existe déjà
IF OBJECT_ID('dbo.WEB_GMAO_REPARATION', 'U') IS NOT NULL
BEGIN
    PRINT '⚠️ La table WEB_GMAO_REPARATION existe déjà.'
    PRINT 'Pour recréer la table, supprimez-la d''abord avec: DROP TABLE WEB_GMAO_REPARATION;'
    RETURN
END
GO

-- Créer la table WEB_GMAO_REPARATION
PRINT '📝 Création de la table WEB_GMAO_REPARATION...'
CREATE TABLE dbo.WEB_GMAO_REPARATION (
    -- Clé primaire
    ID INT IDENTITY(1,1) PRIMARY KEY,
    
    -- Informations de réparation
    DteDeb DATETIME NULL,
    DteFin DATETIME NULL,
    TpsReel AS (CASE 
        WHEN DteDeb IS NOT NULL AND DteFin IS NOT NULL 
        THEN CAST(DATEDIFF(MINUTE, DteDeb, DteFin) AS FLOAT) / 60.0 
        ELSE NULL 
    END) PERSISTED,  -- Colonne calculée persistée
    Nat VARCHAR(4) NULL CHECK (Nat IN ('Mec', 'Elec')),
    ID_StatRep TINYINT NULL,
    TypeIN CHAR(1) NULL CHECK (TypeIN IN ('R','P')) DEFAULT 'R',
    MatInter INT NULL,
    Intervenant NVARCHAR(101) NULL,
    
    -- Lien vers la demande d'intervention
    ID_WEB_GMAO_Dem_In INT NULL,
    
    -- Machine concernée
    PostesReel VARCHAR(50) NULL,
    
    -- Métadonnées
    DateCreation DATETIME DEFAULT GETDATE(),
    DateModification DATETIME DEFAULT GETDATE(),
    
    -- Contraintes
    CONSTRAINT FK_WEB_GMAO_REPARATION_WEB_GMAO 
        FOREIGN KEY (ID_WEB_GMAO_Dem_In) REFERENCES WEB_GMAO(ID) ON DELETE SET NULL,
    
    CONSTRAINT FK_WEB_GMAO_REPARATION_StatRep 
        FOREIGN KEY (ID_StatRep) REFERENCES WEB_GMAO_StatRep(ID),
    
    CONSTRAINT FK_WEB_GMAO_REPARATION_Intervenant 
        FOREIGN KEY (MatInter) REFERENCES personel(Matricule),
    
    -- Contrainte : Si ID_WEB_GMAO_Dem_In est NULL, alors ID_StatRep doit être NULL
    CONSTRAINT CK_WEB_GMAO_REPARATION_StatRep_When_DemIn_Null
        CHECK (ID_WEB_GMAO_Dem_In IS NOT NULL OR ID_StatRep IS NULL)
);
GO

-- Créer des index pour améliorer les performances
PRINT '📝 Création des index...'
CREATE NONCLUSTERED INDEX IX_WEB_GMAO_REPARATION_ID_WEB_GMAO_Dem_In 
    ON dbo.WEB_GMAO_REPARATION(ID_WEB_GMAO_Dem_In);
GO

CREATE NONCLUSTERED INDEX IX_WEB_GMAO_REPARATION_MatInter 
    ON dbo.WEB_GMAO_REPARATION(MatInter);
GO

CREATE NONCLUSTERED INDEX IX_WEB_GMAO_REPARATION_ID_StatRep 
    ON dbo.WEB_GMAO_REPARATION(ID_StatRep);
GO

-- Migrer les données existantes depuis WEB_GMAO
PRINT '📝 Migration des données depuis WEB_GMAO...'
INSERT INTO dbo.WEB_GMAO_REPARATION (
    DteDeb,
    DteFin,
    Nat,
    ID_StatRep,
    MatInter,
    Intervenant,
    ID_WEB_GMAO_Dem_In,
    PostesReel,
    DateCreation,
    DateModification
)
SELECT 
    g.DteDeb,
    g.DteFin,
    g.Nat,
    g.ID_StatRep,
    g.MatInter,
    g.Internvenant,
    g.ID as ID_WEB_GMAO_Dem_In,  -- Lier à la demande d'intervention
    g.PostesReel,
    g.DateCreation,
    g.DateModification
FROM WEB_GMAO g
WHERE g.DteDeb IS NOT NULL 
   OR g.DteFin IS NOT NULL 
   OR g.MatInter IS NOT NULL 
   OR g.ID_StatRep IS NOT NULL
   OR g.Nat IS NOT NULL;
GO

PRINT '✅ Migration terminée!'
PRINT ''
PRINT '📊 Statistiques:'
SELECT 
    COUNT(*) as NombreReparations,
    COUNT(ID_WEB_GMAO_Dem_In) as AvecDemandeIntervention,
    COUNT(*) - COUNT(ID_WEB_GMAO_Dem_In) as SansDemandeIntervention
FROM WEB_GMAO_REPARATION;
GO

PRINT ''
PRINT '✅ Table WEB_GMAO_REPARATION créée avec succès!'
PRINT ''
PRINT '📌 Structure de la table:'
PRINT '   - ID : Identifiant unique (IDENTITY)'
PRINT '   - DteDeb : Date/heure de début'
PRINT '   - DteFin : Date/heure de fin'
PRINT '   - TpsReel : Temps réel calculé (colonne calculée persistée)'
PRINT '   - Nat : Nature (Mec/Elec)'
PRINT '   - ID_StatRep : Statut de la réparation'
PRINT '   - MatInter : Matricule intervenant'
PRINT '   - Intervenant : Nom et prénom intervenant'
PRINT '   - ID_WEB_GMAO_Dem_In : Lien vers demande d''intervention'
PRINT '   - PostesReel : Machine concernée'
PRINT ''
PRINT '⚠️ IMPORTANT: Les colonnes de réparation dans WEB_GMAO doivent maintenant'
PRINT '   être supprimées ou rendues obsolètes. Le code Python doit être mis à jour'
PRINT '   pour utiliser WEB_GMAO_REPARATION au lieu de WEB_GMAO pour les réparations.'
GO

