# Guide de Configuration - Connexion au Serveur Réseau 192.168.10.225

## Situation actuelle

- ✅ `db.py` configuré pour utiliser `SERVER: "192.168.10.225"`
- ❌ L'authentification Windows ne fonctionne pas avec l'IP
- ⏳ Il faut configurer l'authentification SQL Server

## Étapes à suivre

### Étape 1: Configurer l'authentification SQL Server sur le serveur

**Sur le serveur SQL Server (192.168.10.225)** :

1. Ouvrir SQL Server Management Studio (SSMS)
2. Se connecter au serveur
3. Clic droit sur le serveur → **Propriétés**
4. Onglet **Sécurité**
5. Cocher **Mode d'authentification SQL Server et Windows** (mode mixte)
6. Cliquer sur **OK** et redémarrer le service SQL Server si demandé

### Étape 2: Créer un utilisateur SQL Server

1. Dans SSMS, se connecter au serveur
2. **Sécurité** → **Connexions** → Clic droit → **Nouvelle connexion**
3. Remplir :
   - **Nom de connexion** : (ex: `novaprint_app`)
   - **Authentification SQL Server**
   - **Mot de passe** : (choisir un mot de passe sécurisé)
   - Décocher **L'utilisateur doit changer le mot de passe à la prochaine connexion**
4. Onglet **Mappage des utilisateurs** :
   - Cocher la base de données `novaprint_restored`
   - Rôle de base de données : `db_datareader`, `db_datawriter`, `db_ddladmin`
5. Cliquer sur **OK**

### Étape 3: Configurer db.py avec les credentials

**Option A: Utiliser le script automatique**

```bash
cd C:\Apps
.\venv\Scripts\Activate.ps1
python configurer_db_avec_credentials.py novaprint_app VotreMotDePasse
```

**Option B: Modifier manuellement db.py**

Ouvrir `C:\Apps\db.py` et modifier :

```python
DB_CONFIG = {
    "DRIVER": "{SQL Server}",
    "SERVER": "192.168.10.225",
    "DATABASE": "novaprint_restored",
    "UID": "novaprint_app",  # Votre utilisateur SQL Server
    "PWD": "VotreMotDePasse",  # Votre mot de passe
    "TrustServerCertificate": "yes"
    # RETIRER "Trusted_Connection": "yes"
}
```

### Étape 4: Tester la connexion

```bash
cd C:\Apps
.\venv\Scripts\Activate.ps1
python verifier_config_flask.py
```

Vous devriez voir :
```
[OK] Connexion reussie!
  Serveur SQL: [nom du serveur]
  Base de donnees: novaprint_restored
[OK] Connexion au serveur RESEAU confirmee!
```

### Étape 5: Créer la table WEB_S_DOS_ENCOURS

```bash
cd C:\Apps
.\venv\Scripts\Activate.ps1
python creer_table_final.py
```

### Étape 6: Synchroniser les fichiers

```powershell
Copy-Item "C:\Apps\db.py" "X:\db.py" -Force
```

### Étape 7: Redémarrer Flask

Redémarrer l'application Flask pour charger la nouvelle configuration.

## Scripts disponibles

- `configurer_db_avec_credentials.py` : Configure db.py avec username/password
- `verifier_config_flask.py` : Vérifie quelle base est utilisée
- `creer_table_final.py` : Crée la table WEB_S_DOS_ENCOURS sur le serveur réseau

## Vérification finale

Après configuration, vérifier que :

1. ✅ La connexion fonctionne vers 192.168.10.225
2. ✅ La table WEB_S_DOS_ENCOURS existe sur le serveur réseau
3. ✅ Toutes les opérations CRUD du Projet 19 pointent vers le serveur réseau
4. ✅ Aucune donnée n'est créée sur la base locale

## Dépannage

### Erreur: "Impossible de générer le contexte SSPI"
- **Cause** : Authentification Windows ne fonctionne pas avec l'IP
- **Solution** : Utiliser l'authentification SQL Server (UID/PWD)

### Erreur: "Login failed for user"
- **Cause** : Credentials incorrects ou utilisateur n'existe pas
- **Solution** : Vérifier les credentials et que l'utilisateur existe

### Erreur: "Cannot open database"
- **Cause** : L'utilisateur n'a pas les permissions sur la base
- **Solution** : Donner les permissions db_datareader, db_datawriter, db_ddladmin




