# Problème de connexion au serveur réseau 192.168.10.225

## Situation actuelle

- ❌ La table `WEB_S_DOS_ENCOURS` est créée sur la base **locale** (PC)
- ❌ Elle n'existe pas sur le serveur réseau **192.168.10.225**
- ❌ L'authentification Windows ne fonctionne pas avec l'IP 192.168.10.225

## Configuration actuelle dans db.py

Le fichier `C:\Apps\db.py` a été modifié pour utiliser :
```python
"SERVER": "192.168.10.225"
```

Mais l'authentification Windows (`Trusted_Connection`) ne fonctionne pas avec une adresse IP.

## Solutions possibles

### Solution 1: Configurer l'authentification SQL Server (RECOMMANDÉ)

1. **Sur le serveur SQL Server (192.168.10.225)** :
   - Activer l'authentification SQL Server (mode mixte)
   - Créer un utilisateur SQL Server avec les permissions nécessaires

2. **Modifier `C:\Apps\db.py`** :
```python
DB_CONFIG = {
    "DRIVER": "{SQL Server}",
    "SERVER": "192.168.10.225",
    "DATABASE": "novaprint_restored",
    "UID": "username_sql",  # Utilisateur SQL Server
    "PWD": "password_sql",  # Mot de passe SQL Server
    "TrustServerCertificate": "yes"
    # RETIRER "Trusted_Connection": "yes"
}
```

### Solution 2: Utiliser le nom du serveur si l'authentification Windows fonctionne

Si l'authentification Windows fonctionne avec le nom du serveur :

```python
DB_CONFIG = {
    "DRIVER": "{SQL Server}",
    "SERVER": "SRV-KBA1",  # Correspond à 192.168.10.225
    "DATABASE": "novaprint_restored",
    "Trusted_Connection": "yes",
    "TrustServerCertificate": "yes"
}
```

**MAIS** : Il faut vérifier que SRV-KBA1 pointe bien vers le serveur réseau et pas vers la base locale.

### Solution 3: Vérifier quelle configuration fonctionne actuellement

L'application Flask doit se connecter quelque part pour fonctionner. Il faut identifier quelle configuration fonctionne :

1. Vérifier les logs Flask
2. Vérifier quelle base de données est réellement utilisée
3. Identifier pourquoi elle se connecte à la base locale

## Actions immédiates

1. ✅ **db.py modifié** pour utiliser `192.168.10.225`
2. ⏳ **Configurer l'authentification SQL Server** sur le serveur réseau
3. ⏳ **Tester la connexion** avec les nouvelles credentials
4. ⏳ **Créer la table** `WEB_S_DOS_ENCOURS` sur le serveur réseau
5. ⏳ **Vérifier** que toutes les opérations pointent vers le serveur réseau

## Fichiers modifiés

- ✅ `C:\Apps\db.py` : Configuration SERVER = "192.168.10.225"
- ✅ `X:\db.py` : Synchronisé
- ✅ Scripts de test créés pour vérifier la connexion

## Prochaines étapes

**URGENT** : Configurer l'authentification SQL Server sur le serveur 192.168.10.225 et mettre à jour `db.py` avec les credentials.




