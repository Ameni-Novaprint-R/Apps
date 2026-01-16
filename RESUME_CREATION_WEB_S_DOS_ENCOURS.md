# Résumé de la création de la table WEB_S_DOS_ENCOURS

## ✅ Table créée avec succès

**Base de données:** `NOVAPRINT_restored`  
**Table:** `WEB_S_DOS_ENCOURS`  
**Lignes insérées:** 1458

## Structure de la table

| Colonne | Type | Description | Source |
|---------|------|------------|--------|
| `ID` | INT IDENTITY(1,1) PRIMARY KEY | Identifiant unique | Auto-généré |
| `Numero_COMMANDES` | NVARCHAR(255) | Numéro de dossier | `COMMANDES.Numero` |
| `RaiSocTri_SOCIETES` | NVARCHAR(255) | Raison sociale du client | `SOCIETES.RaiSocTri` (via `COMMANDES.ID_SOCIETE = SOCIETES.ID`) |
| `Reference_COMMANDES` | NVARCHAR(255) | Référence/Désignation | `COMMANDES.Reference` |
| `QteComm_COMMANDES` | INT | Quantité | `COMMANDES.QteComm` |
| `Coef_COMMANDES` | DECIMAL(18,2) | Coefficient/Marge | `COMMANDES.Coef` |
| `DateCreation` | DATETIME | Date de création | GETDATE() |
| `DateModification` | DATETIME | Date de modification | GETDATE() |

## Index créé

- **IX_WEB_S_DOS_ENCOURS_Numero** sur `Numero_COMMANDES` pour améliorer les performances de recherche

## Règles respectées

✅ **Données initiales copiées** depuis `COMMANDES` et `SOCIETES`  
✅ **Tables source protégées** : `COMMANDES` et `SOCIETES` restent strictement inchangées  
✅ **Modifications uniquement dans WEB_S_DOS_ENCOURS** : Toute création, modification ou suppression se fait uniquement dans cette table

## Fonctions Python ajoutées dans `db.py`

### `get_web_s_dos_encours(search_numero=None)`
Récupère les dossiers en cours depuis `WEB_S_DOS_ENCOURS`.  
Si `search_numero` est fourni, recherche les dossiers dont le numéro contient cette valeur (recherche de type "contient").

### `get_web_s_dos_encours_by_numero(numero)`
Récupère un dossier en cours par son numéro exact.

### `update_web_s_dos_encours_quantite(id_dossier, nouvelle_quantite)`
Met à jour la quantité d'un dossier. **Seule la quantité peut être modifiée** selon les spécifications.

### `create_web_s_dos_encours(numero, client=None, reference=None, quantite=None, marge=None)`
Crée un nouveau dossier dans `WEB_S_DOS_ENCOURS`.  
Si les données ne sont pas fournies, elles sont automatiquement récupérées depuis `COMMANDES` et `SOCIETES`.

### `delete_web_s_dos_encours(id_dossier)`
Supprime un dossier de `WEB_S_DOS_ENCOURS`.

## Comportement de l'application (spécifications)

| Champ | Colonne | Comportement |
|-------|---------|--------------|
| **N° de dossier** | `Numero_COMMANDES` | Recherche de type "contient" |
| **Client** | `RaiSocTri_SOCIETES` | Affiché automatiquement après sélection du N° de dossier |
| **Désignation** | `Reference_COMMANDES` | Affiché automatiquement, **non modifiable** |
| **Quantité** | `QteComm_COMMANDES` | Affiché par défaut et automatiquement, **modifiable** |
| **Marge** | `Coef_COMMANDES` | Affiché automatiquement, **non modifiable** |

## Fichiers créés

1. **`create_web_s_dos_encours.sql`** : Script SQL pour créer la table
2. **`create_web_s_dos_encours.py`** : Script Python pour créer la table et copier les données
3. **`db.py`** : Fonctions Python ajoutées pour gérer la table

## Prochaines étapes

Pour utiliser cette table dans l'application web :
1. Créer les routes Flask dans `routes/` pour exposer les fonctionnalités
2. Créer les templates HTML pour l'interface utilisateur
3. Implémenter la logique de recherche "contient" pour le champ N° de dossier
4. S'assurer que seuls les champs modifiables (Quantité) peuvent être modifiés




