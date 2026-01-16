# Instructions - Vérification et Création de WEB_S_DOS_ENCOURS

## Objectif

Vérifier que la table `WEB_S_DOS_ENCOURS` existe sur le serveur réseau **192.168.10.225** et la créer si nécessaire.

**IMPORTANT** : La table doit être **UNIQUEMENT** sur le serveur réseau, pas en local.

## Méthode 1: Script Python (si l'authentification fonctionne)

```bash
cd C:\Apps
.\venv\Scripts\Activate.ps1
python verifier_creer_web_s_dos_encours_avec_auth.py
```

## Méthode 2: Script SQL direct (Recommandé)

Si l'authentification Python ne fonctionne pas, exécuter le script SQL directement sur le serveur :

1. **Se connecter au serveur SQL Server 192.168.10.225** avec SQL Server Management Studio (SSMS)
2. **Ouvrir** le fichier `verifier_creer_web_s_dos_encours_sql.sql`
3. **Exécuter** le script dans SSMS

Le script :
- ✅ Vérifie si la table existe
- ✅ Affiche la structure si elle existe
- ✅ Crée la table si elle n'existe pas
- ✅ Crée l'index nécessaire

## Méthode 3: Avec authentification SQL Server

Si vous avez configuré l'authentification SQL Server :

```bash
# Définir les variables d'environnement
$env:SQL_SERVER_USER = "votre_username"
$env:SQL_SERVER_PWD = "votre_password"

# Exécuter le script
python verifier_creer_web_s_dos_encours_avec_auth.py
```

## Structure de la table

La table `WEB_S_DOS_ENCOURS` doit avoir la structure suivante :

```sql
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
```

## Vérification qu'aucune table n'existe localement

Pour vérifier qu'aucune table équivalente n'existe localement :

1. **Se connecter à la base locale** (si elle existe)
2. **Vérifier** :
   ```sql
   SELECT * FROM INFORMATION_SCHEMA.TABLES 
   WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS'
   ```
3. **Si la table existe localement** : La supprimer (elle ne doit être que sur le serveur réseau)

## Fichiers disponibles

- `verifier_creer_web_s_dos_encours_avec_auth.py` : Script Python avec support de plusieurs méthodes d'authentification
- `verifier_creer_web_s_dos_encours_sql.sql` : Script SQL à exécuter directement sur le serveur
- `verifier_creer_web_s_dos_encours.py` : Script Python utilisant la configuration de db.py

## Résultat attendu

Après exécution, vous devriez voir :

```
[OK] Connexion au serveur RESEAU confirmee!
[OK] La table WEB_S_DOS_ENCOURS existe sur le serveur reseau
  OU
[OK] Table WEB_S_DOS_ENCOURS creee sur le serveur reseau!
```

**La table doit être uniquement sur 192.168.10.225, pas en local.**




