/*
================================================================================
AJOUT DE COLONNES À LA TABLE personel
================================================================================
Objectif : Ajouter les colonnes suivantes à la table personel :
- id : identifiant technique unique (PRIMARY KEY, AUTO_INCREMENT)
- mdp : mot de passe haché avec bcrypt
- archive : indicateur d'archivage (0 par défaut, 1 si archivé)
================================================================================
*/

USE [novaprint_restored]
GO

PRINT '📝 Début de la modification de la table personel...'
PRINT ''

-- ============================================================================
-- ÉTAPE 1 : Vérifier et ajouter la colonne id
-- ============================================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'personel' AND COLUMN_NAME = 'id')
BEGIN
    PRINT '📝 Ajout de la colonne id...'
    
    -- Vérifier si une clé primaire existe déjà
    DECLARE @PKName NVARCHAR(128)
    SELECT @PKName = name
    FROM sys.key_constraints
    WHERE type = 'PK' 
      AND parent_object_id = OBJECT_ID('dbo.personel')
    
    -- Si une clé primaire existe, la supprimer temporairement
    IF @PKName IS NOT NULL
    BEGIN
        PRINT '⚠️  Une clé primaire existe déjà (' + @PKName + ').'
        PRINT '    Suppression temporaire de la clé primaire...'
        
        DECLARE @sql NVARCHAR(MAX) = 'ALTER TABLE dbo.personel DROP CONSTRAINT ' + QUOTENAME(@PKName)
        EXEC sp_executesql @sql
        PRINT '    ✅ Clé primaire supprimée temporairement'
    END
    
    -- Ajouter la colonne id avec IDENTITY
    ALTER TABLE dbo.personel 
    ADD id INT IDENTITY(1,1) NOT NULL
    
    -- Définir id comme nouvelle clé primaire
    ALTER TABLE dbo.personel 
    ADD CONSTRAINT PK_personel_id PRIMARY KEY (id)
    
    PRINT '✅ Colonne id ajoutée avec IDENTITY(1,1) et définie comme PRIMARY KEY'
    
    -- Si Matricule était la clé primaire, créer une contrainte UNIQUE sur Matricule
    IF @PKName IS NOT NULL
    BEGIN
        -- Vérifier si une contrainte UNIQUE existe déjà sur Matricule
        IF NOT EXISTS (SELECT * FROM sys.key_constraints 
                       WHERE type = 'UQ' 
                         AND parent_object_id = OBJECT_ID('dbo.personel')
                         AND name LIKE '%Matricule%')
        BEGIN
            ALTER TABLE dbo.personel 
            ADD CONSTRAINT UQ_personel_Matricule UNIQUE (Matricule)
            PRINT '✅ Contrainte UNIQUE créée sur Matricule'
        END
        ELSE
        BEGIN
            PRINT 'ℹ️  Une contrainte UNIQUE existe déjà sur Matricule'
        END
    END
END
ELSE
BEGIN
    PRINT '⚠️  La colonne id existe déjà'
END
GO

-- ============================================================================
-- ÉTAPE 2 : Ajouter la colonne mdp (mot de passe haché avec bcrypt)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'personel' AND COLUMN_NAME = 'mdp')
BEGIN
    PRINT '📝 Ajout de la colonne mdp...'
    ALTER TABLE dbo.personel 
    ADD mdp VARCHAR(60) NULL  -- bcrypt produit des hash de 60 caractères
    PRINT '✅ Colonne mdp ajoutée (VARCHAR(60) pour stocker le hash bcrypt)'
END
ELSE
BEGIN
    PRINT '⚠️  La colonne mdp existe déjà'
END
GO

-- ============================================================================
-- ÉTAPE 3 : Ajouter la colonne archive
-- ============================================================================
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'personel' AND COLUMN_NAME = 'archive')
BEGIN
    PRINT '📝 Ajout de la colonne archive...'
    ALTER TABLE dbo.personel 
    ADD archive TINYINT NOT NULL DEFAULT 0  -- 0 = actif, 1 = archivé
    PRINT '✅ Colonne archive ajoutée (TINYINT, DEFAULT 0)'
    
    -- Mettre à jour les valeurs existantes à 0 si elles sont NULL
    UPDATE dbo.personel 
    SET archive = 0 
    WHERE archive IS NULL
    PRINT '✅ Valeurs existantes initialisées à 0'
END
ELSE
BEGIN
    PRINT '⚠️  La colonne archive existe déjà'
END
GO

-- ============================================================================
-- RÉSUMÉ FINAL
-- ============================================================================
PRINT ''
PRINT '✅ Modification de la table personel terminée!'
PRINT ''
PRINT '📌 Colonnes ajoutées:'
PRINT '   - id : INT IDENTITY(1,1) PRIMARY KEY'
PRINT '   - mdp : VARCHAR(60) NULL (pour stocker le hash bcrypt)'
PRINT '   - archive : TINYINT NOT NULL DEFAULT 0 (0 = actif, 1 = archivé)'
PRINT ''
PRINT '📊 Structure actuelle de la table personel:'
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    CASE 
        WHEN COLUMNPROPERTY(OBJECT_ID('dbo.personel'), COLUMN_NAME, 'IsIdentity') = 1 
        THEN 'OUI' 
        ELSE 'NON' 
    END AS IS_IDENTITY
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'personel'
ORDER BY ORDINAL_POSITION
GO
