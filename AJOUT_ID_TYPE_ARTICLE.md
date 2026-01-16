# ✅ Ajout de la Colonne ID_GS_TYPES_ARTICLE

## 🎯 Objectif

Ajouter une colonne `ID_GS_TYPES_ARTICLE` dans la table `WEB_GMAO_ARTICLES` pour stocker l'ID du type d'article (2 ou 8) sans modifier la table source `GS_TYPES_ARTICLE`.

---

## 🗄️ Modifications de la Base de Données

### 1. **Nouvelle Colonne**

```sql
ALTER TABLE WEB_GMAO_ARTICLES
ADD ID_GS_TYPES_ARTICLE INT NULL;
```

**Caractéristiques** :
- Type : `INT`
- Nullable : `NULL` (pour compatibilité avec données existantes)
- Valeurs possibles : 2 (PDTS CHIMIQUES) ou 8 (PIECES DE RECHANGE)

### 2. **Remplissage des Valeurs Existantes**

```sql
UPDATE wa
SET wa.ID_GS_TYPES_ARTICLE = t.ID
FROM WEB_GMAO_ARTICLES wa
INNER JOIN GS_ARTICLES a ON wa.ID_GS_ARTICLES = a.ID
INNER JOIN GS_FAMILLES f ON a.ID_FAMILLE = f.ID
INNER JOIN GS_TYPES_ARTICLE t ON f.ID_TYPE_ARTICLE = t.ID
WHERE wa.ID_GS_ARTICLES IS NOT NULL;
```

**Résultat** : 24 lignes mises à jour

### 3. **Index de Performance**

```sql
CREATE NONCLUSTERED INDEX IX_WEB_GMAO_ARTICLES_ID_GS_TYPES_ARTICLE 
    ON WEB_GMAO_ARTICLES(ID_GS_TYPES_ARTICLE);
```

---

## 🔄 Synchronisation Automatique

### Triggers Mis à Jour

#### 1. **Trigger INSERT sur WEB_GMAO_ARTICLES**
```sql
CREATE TRIGGER TR_WEB_GMAO_ARTICLES_SYNC_INSERT
ON WEB_GMAO_ARTICLES
AFTER INSERT
AS
BEGIN
    UPDATE wa
    SET 
        wa.Designation_GS_ARTICLES = a.Designation,
        wa.Designation_GS_FAMILLES = f.Designation,
        wa.Designation_GS_TYPES_ARTICLE = t.Designation,
        wa.ID_GS_TYPES_ARTICLE = t.ID  -- ← NOUVEAU
    FROM WEB_GMAO_ARTICLES wa
    INNER JOIN INSERTED i ON wa.ID = i.ID
    LEFT JOIN GS_ARTICLES a ON wa.ID_GS_ARTICLES = a.ID
    LEFT JOIN GS_FAMILLES f ON a.ID_FAMILLE = f.ID
    LEFT JOIN GS_TYPES_ARTICLE t ON f.ID_TYPE_ARTICLE = t.ID
    WHERE wa.ID_GS_ARTICLES IS NOT NULL;
END;
```

#### 2. **Trigger UPDATE sur GS_ARTICLES**
Synchronise quand un article change de famille ou de désignation.

#### 3. **Trigger UPDATE sur GS_FAMILLES**
Synchronise quand une famille change de type.

#### 4. **Trigger UPDATE sur GS_TYPES_ARTICLE**
Synchronise quand la désignation d'un type change (pas l'ID).

---

## 📊 Structure Complète

### Relations entre Tables

```
GS_ARTICLES
    ├─→ GS_FAMILLES (via ID_FAMILLE)
        └─→ GS_TYPES_ARTICLE (via ID_TYPE_ARTICLE)

WEB_GMAO_ARTICLES (copie des données)
    ├─ ID_GS_ARTICLES (FK vers GS_ARTICLES)
    ├─ Designation_GS_ARTICLES (copie)
    ├─ Designation_GS_FAMILLES (copie)
    ├─ Designation_GS_TYPES_ARTICLE (copie)
    └─ ID_GS_TYPES_ARTICLE (copie) ← NOUVEAU
```

### Colonnes de WEB_GMAO_ARTICLES

| Colonne | Type | Description |
|---------|------|-------------|
| `ID` | INT IDENTITY | Clé primaire auto-incrémentée |
| `ID_WEB_GMAO` | INT | Référence à la fiche de réparation |
| `ID_GS_ARTICLES` | INT | Référence à l'article source |
| `Designation_GS_ARTICLES` | VARCHAR(200) | Copie de la désignation |
| `Designation_GS_FAMILLES` | VARCHAR(100) | Copie de la famille |
| `Designation_GS_TYPES_ARTICLE` | VARCHAR(100) | Copie du type |
| **`ID_GS_TYPES_ARTICLE`** | **INT** | **Copie de l'ID du type** ← NOUVEAU |
| `Quantite` | DECIMAL(10,3) | Quantité utilisée |
| `DateCreation` | DATETIME | Date de création |
| `DateModification` | DATETIME | Date de modification |

---

## 🧪 Test de Validation

### Résultats du Test

```
Fiche de test : ID 154
Article Type 2 (PDTS CHIMIQUES) : ID 222
  → ID_GS_TYPES_ARTICLE = 2 ✅

Article Type 8 (PIECES DE RECHANGE) : ID 223
  → ID_GS_TYPES_ARTICLE = 8 ✅
```

### Répartition Actuelle

| ID_Type | Désignation | Nombre d'Articles |
|---------|-------------|-------------------|
| 2 | PDTS CHIMIQUES | 5 |
| 8 | PIECES DE RECHANGE | 19 |

---

## 💡 Utilisation

### Filtrer par Type d'Article

```sql
-- Articles de type 2 (Produits chimiques)
SELECT * FROM WEB_GMAO_ARTICLES
WHERE ID_GS_TYPES_ARTICLE = 2;

-- Articles de type 8 (Pièces de rechange)
SELECT * FROM WEB_GMAO_ARTICLES
WHERE ID_GS_TYPES_ARTICLE = 8;

-- Statistiques par type
SELECT 
    ID_GS_TYPES_ARTICLE,
    Designation_GS_TYPES_ARTICLE,
    COUNT(*) as NombreUtilisations,
    SUM(Quantite) as QuantiteTotale
FROM WEB_GMAO_ARTICLES
GROUP BY ID_GS_TYPES_ARTICLE, Designation_GS_TYPES_ARTICLE;
```

### Backend Python

```python
# Récupérer les articles avec leur type
articles = get_articles_by_fiche(fiche_id)

for art in articles:
    print(f"Article: {art['designation']}")
    print(f"Type ID: {art['id_type']}")  # 2 ou 8
    print(f"Type: {art['type']}")  # Désignation
```

---

## 📋 Règles Importantes

### ✅ À FAIRE
- Utiliser `ID_GS_TYPES_ARTICLE` pour filtrer les articles
- Consulter la colonne pour des statistiques
- Utiliser dans les requêtes JOIN si nécessaire

### ❌ À NE PAS FAIRE
- Modifier `GS_TYPES_ARTICLE` depuis la page web
- Modifier manuellement `ID_GS_TYPES_ARTICLE` (géré par triggers)
- Insérer des valeurs autres que 2 ou 8

---

## ✅ Validation

- ✅ Colonne ajoutée
- ✅ Valeurs existantes remplies (24 articles)
- ✅ Index créé
- ✅ 4 triggers mis à jour/créés
- ✅ Synchronisation automatique fonctionnelle
- ✅ Test unitaire passé
- ✅ Backend mis à jour (`get_articles_by_fiche`)

**Status** : Déployé et opérationnel 🎉




















