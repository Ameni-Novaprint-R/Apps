# Instructions pour configurer la connexion vers le serveur 192.168.10.225

## Problème identifié

La table `WEB_S_DOS_ENCOURS` est créée sur la base locale au lieu du serveur réseau 192.168.10.225.

## Solution

### Option 1: Utiliser l'authentification SQL Server (Recommandé)

Si l'authentification Windows ne fonctionne pas avec l'IP 192.168.10.225, modifier `db.py` :

```python
DB_CONFIG = {
    "DRIVER": "{SQL Server}",
    "SERVER": "192.168.10.225",
    "DATABASE": "novaprint_restored",
    "UID": "username_sql_server",  # Utilisateur SQL Server
    "PWD": "password_sql_server",  # Mot de passe SQL Server
    "TrustServerCertificate": "yes"
    # RETIRER "Trusted_Connection": "yes"
}
```

### Option 2: Utiliser le nom du serveur avec authentification Windows

Si SRV-KBA1 fonctionne avec l'authentification Windows :

```python
DB_CONFIG = {
    "DRIVER": "{SQL Server}",
    "SERVER": "SRV-KBA1",  # Correspond à 192.168.10.225
    "DATABASE": "novaprint_restored",
    "Trusted_Connection": "yes",
    "TrustServerCertificate": "yes"
}
```

### Option 3: Vérifier la configuration actuelle

Pour vérifier quelle base de données est utilisée :

1. Exécuter Flask
2. Accéder à une route qui utilise la base de données
3. Vérifier les logs ou utiliser un script de test

## Fichiers modifiés

- ✅ `C:\Apps\db.py` : Configuration SERVER mise à jour vers 192.168.10.225
- ✅ `X:\db.py` : Synchronisé avec C:\Apps\db.py

## Prochaines étapes

1. **Tester la connexion** avec la nouvelle configuration
2. **Si l'authentification Windows échoue**, configurer l'authentification SQL Server
3. **Créer la table** `WEB_S_DOS_ENCOURS` sur le serveur réseau
4. **Vérifier** que toutes les opérations CRUD pointent vers le serveur réseau

## Scripts disponibles

- `test_connexion_serveur.py` : Tester différentes configurations
- `verifier_base_actuelle.py` : Vérifier quelle base est utilisée
- `create_web_s_dos_encours.py` : Créer la table (utilisera la config de db.py)




