# Politique de Gestion des Tables Applicatives

## Principe fondamental

**TOUTES les tables applicatives doivent être créées et gérées EXCLUSIVEMENT sur le serveur réseau 192.168.10.225.**

**AUCUNE table applicative ne doit être créée localement sur le PC.**

## Tables applicatives identifiées

Les tables suivantes sont considérées comme applicatives et doivent être sur le serveur réseau :

1. **WEB_S_DOS_ENCOURS** - Gestion des dossiers en cours (Projet 19)
2. **WEB_GMAO_REPARATION** - GMAO réparations (Projet 16)
3. **CONTROLES_QUALITE** - Contrôles qualité (Projet 10)
4. **VOYAGES** - Programme de voyage (Projet 6)
5. **VOYAGE_LIGNES** - Lignes de voyage (Projet 6)

## Règles strictes

### ✅ À FAIRE

- ✅ Toutes les opérations CRUD pointent vers `SERVER: "192.168.10.225"`
- ✅ Toutes les fonctions `CREATE TABLE` utilisent la syntaxe SQL Server
- ✅ Toutes les tables sont créées avec `IF NOT EXISTS` (syntaxe SQL Server)
- ✅ Tous les scripts de création utilisent la configuration de `db.py`

### ❌ À NE PAS FAIRE

- ❌ Créer des tables localement sur le PC
- ❌ Utiliser la syntaxe SQLite (`AUTOINCREMENT`, `TEXT`, etc.)
- ❌ Utiliser une configuration de serveur local
- ❌ Créer des tables sans vérifier qu'elles pointent vers le serveur réseau

## Configuration requise

### db.py

```python
DB_CONFIG = {
    "DRIVER": "{SQL Server}",
    "SERVER": "192.168.10.225",  # Serveur réseau - OBLIGATOIRE
    "DATABASE": "novaprint_restored",
    # Authentification SQL Server (UID/PWD) ou Windows selon configuration
}
```

### Syntaxe SQL Server

**❌ INCORRECT (SQLite)** :
```sql
CREATE TABLE IF NOT EXISTS VOYAGES (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    ...
)
```

**✅ CORRECT (SQL Server)** :
```sql
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'VOYAGES')
BEGIN
    CREATE TABLE VOYAGES (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        ...
    )
END
```

## Scripts de vérification

### 1. Vérifier la configuration

```bash
python verifier_config_flask.py
```

### 2. Auditer toutes les tables

```bash
python audit_tables_applicatives.py
```

### 3. Créer toutes les tables sur le serveur réseau

```bash
python creer_toutes_tables_serveur.py
```

## Fonctions corrigées

### ✅ `init_projet6_tables()`

**Avant** : Utilisait la syntaxe SQLite
**Après** : Utilise la syntaxe SQL Server et pointe vers le serveur réseau

## Vérification continue

Avant chaque création de table applicative :

1. ✅ Vérifier que `db.py` pointe vers `192.168.10.225`
2. ✅ Vérifier que la syntaxe est SQL Server (pas SQLite)
3. ✅ Tester la connexion au serveur réseau
4. ✅ Vérifier que la table est créée sur le serveur réseau (pas localement)

## En cas de problème

Si une table est créée localement par erreur :

1. **Identifier** : Utiliser `audit_tables_applicatives.py`
2. **Migrer** : Créer la table sur le serveur réseau
3. **Supprimer** : Supprimer la table de la base locale
4. **Vérifier** : Confirmer que tout fonctionne sur le serveur réseau




