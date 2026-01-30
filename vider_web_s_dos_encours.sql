-- Script SQL pour vider la table WEB_S_DOS_ENCOURS et réinitialiser l'ID
-- Base de données: novaprint_restored
-- Serveur: 192.168.10.225
-- 
-- Ce script:
-- 1. Supprime toutes les données de la table WEB_S_DOS_ENCOURS
-- 2. Réinitialise le compteur IDENTITY pour recommencer la numérotation à partir de 1

USE novaprint_restored;
GO

PRINT '============================================================================';
PRINT 'VIDAGE DE LA TABLE WEB_S_DOS_ENCOURS ET REINITIALISATION DE L''ID';
PRINT '============================================================================';
PRINT '';

-- Compter les lignes avant suppression
DECLARE @count_before INT;
SELECT @count_before = COUNT(*) FROM WEB_S_DOS_ENCOURS;
PRINT 'Nombre de lignes a supprimer: ' + CAST(@count_before AS VARCHAR(10));
PRINT '';

IF @count_before = 0
BEGIN
    PRINT '[INFO] La table WEB_S_DOS_ENCOURS est deja vide.';
    PRINT '';
    PRINT 'Verification de la valeur actuelle de l''IDENTITY...';
    DECLARE @current_identity INT;
    SELECT @current_identity = IDENT_CURRENT('WEB_S_DOS_ENCOURS');
    PRINT 'Valeur actuelle de l''IDENTITY: ' + CAST(@current_identity AS VARCHAR(10));
    PRINT '';
    PRINT 'Reinitialisation de l''ID pour recommencer a partir de 1...';
    DBCC CHECKIDENT('WEB_S_DOS_ENCOURS', RESEED, 0);
    PRINT '[OK] ID reinitialise - Prochain ID sera: 1';
END
ELSE
BEGIN
    -- Vider la table
    PRINT 'Suppression de toutes les lignes...';
    DELETE FROM WEB_S_DOS_ENCOURS;
    PRINT '[OK] ' + CAST(@count_before AS VARCHAR(10)) + ' lignes supprimees';
    PRINT '';
    
    -- Réinitialiser l'ID pour recommencer à partir de 1
    PRINT 'Reinitialisation de l''ID (IDENTITY) pour recommencer a partir de 1...';
    DBCC CHECKIDENT('WEB_S_DOS_ENCOURS', RESEED, 0);
    PRINT '[OK] ID reinitialise - Prochain ID sera: 1';
    PRINT '';
    
    -- Vérifier
    DECLARE @count_after INT;
    SELECT @count_after = COUNT(*) FROM WEB_S_DOS_ENCOURS;
    PRINT 'Nombre de lignes restantes: ' + CAST(@count_after AS VARCHAR(10));
    
    -- Vérifier la valeur actuelle de l'IDENTITY
    DECLARE @current_identity_after INT;
    SELECT @current_identity_after = IDENT_CURRENT('WEB_S_DOS_ENCOURS');
    PRINT 'Valeur actuelle de l''IDENTITY: ' + CAST(@current_identity_after AS VARCHAR(10));
END

PRINT '';
PRINT '============================================================================';
PRINT '[OK] Table WEB_S_DOS_ENCOURS videe avec succes !';
PRINT '[OK] ID reinitialise pour recommencer la numerotation a partir de 1';
PRINT '============================================================================';
GO
