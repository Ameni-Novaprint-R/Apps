# ⚡ CRÉATION IMMÉDIATE - Table WEB_S_DOS_ENCOURS

## 📋 Script SQL Prêt

Le script SQL est créé et prêt à être exécuté : **`CREER_WEB_S_DOS_ENCOURS.sql`**

## 🚀 Méthode Rapide (2 minutes)

### Option 1: SQL Server Management Studio (SSMS) - RECOMMANDÉ

1. **Ouvrir SQL Server Management Studio**
2. **Se connecter au serveur** :
   - Serveur : `192.168.10.225` ou `SRV-KBA1`
   - Authentification : Windows ou SQL Server (selon votre configuration)
3. **Ouvrir le fichier** : `CREER_WEB_S_DOS_ENCOURS.sql`
4. **Vérifier** que la base de données est `novaprint_restored`
5. **Exécuter** le script (F5 ou bouton Exécuter)

### Option 2: Copier-Coller Direct

Copier ce code SQL et l'exécuter dans SSMS :

```sql
USE novaprint_restored;
GO

IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS')
BEGIN
    PRINT 'La table WEB_S_DOS_ENCOURS existe deja.';
    SELECT COUNT(*) AS NombreLignes FROM WEB_S_DOS_ENCOURS;
END
ELSE
BEGIN
    PRINT 'Creation de la table WEB_S_DOS_ENCOURS...';
    
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
    
    CREATE INDEX IX_WEB_S_DOS_ENCOURS_Numero 
    ON WEB_S_DOS_ENCOURS(Numero_COMMANDES);
    
    PRINT 'Table WEB_S_DOS_ENCOURS creee avec succes!';
END
GO

SELECT @@SERVERNAME AS Serveur, DB_NAME() AS BaseDeDonnees;
GO
```

## ✅ Résultat Attendu

Après exécution, vous devriez voir :

```
Creation de la table WEB_S_DOS_ENCOURS...
Table WEB_S_DOS_ENCOURS creee avec succes!
Index IX_WEB_S_DOS_ENCOURS_Numero cree avec succes!
Table creee avec 0 lignes (vide par defaut).
```

## 📍 Localisation

**✅ La table sera créée UNIQUEMENT sur le serveur réseau 192.168.10.225**  
**❌ Aucune table ne sera créée localement**

Le script vérifie automatiquement le serveur avant de créer la table.

## 📁 Fichiers Disponibles

- **`CREER_WEB_S_DOS_ENCOURS.sql`** : Script SQL complet (X:\ et C:\Apps)
- **`INSTRUCTIONS_CREATION_IMMEDIATE.md`** : Instructions détaillées

## ⚡ Action Immédiate

**Exécutez le script SQL dans SSMS maintenant pour créer la table immédiatement !**




