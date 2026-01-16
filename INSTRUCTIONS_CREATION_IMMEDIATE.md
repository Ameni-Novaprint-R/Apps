# Instructions - Création Immédiate de WEB_S_DOS_ENCOURS

## ⚡ Méthode Rapide (RECOMMANDÉE)

### Étape 1: Ouvrir SQL Server Management Studio (SSMS)

1. Lancer **SQL Server Management Studio**
2. Se connecter au serveur **192.168.10.225**
   - **Type de serveur** : Moteur de base de données
   - **Nom du serveur** : `192.168.10.225` ou `SRV-KBA1`
   - **Authentification** : Windows ou SQL Server (selon votre configuration)

### Étape 2: Exécuter le script SQL

1. Ouvrir le fichier **`CREER_WEB_S_DOS_ENCOURS.sql`**
2. Vérifier que la base de données est **`novaprint_restored`**
3. Cliquer sur **Exécuter** (F5)

### Résultat attendu

Vous devriez voir :
```
Creation de la table WEB_S_DOS_ENCOURS...
Table WEB_S_DOS_ENCOURS creee avec succes!
Index IX_WEB_S_DOS_ENCOURS_Numero cree avec succes!
Table creee avec 0 lignes (vide par defaut).
```

## 📋 Contenu du script SQL

Le script :
- ✅ Vérifie si la table existe
- ✅ Crée la table si elle n'existe pas
- ✅ Crée l'index sur Numero_COMMANDES
- ✅ Affiche la structure de la table
- ✅ Confirme que c'est sur le serveur réseau

## ✅ Vérification

Après exécution, vérifier :

```sql
-- Vérifier que la table existe
SELECT * FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS';

-- Vérifier la structure
SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS'
ORDER BY ORDINAL_POSITION;

-- Vérifier le serveur (doit être 192.168.10.225 ou SRV-KBA1)
SELECT @@SERVERNAME AS Serveur, DB_NAME() AS BaseDeDonnees;
```

## 🎯 Résultat

**La table WEB_S_DOS_ENCOURS sera créée UNIQUEMENT sur le serveur réseau 192.168.10.225.**

**Aucune table ne sera créée localement.**




