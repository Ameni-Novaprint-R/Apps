# Plan de Vérification de l'Intégrité - Réalignement PAPIERS_IMPRIMEURS

**Date de création** : 22 janvier 2026  
**Table concernée** : `dbo.PAPIERS_IMPRIMEURS`

---

## Objectif

Vérifier que l'alignement des IDs de `PAPIERS_IMPRIMEURS` avec la base Novaprint a préservé l'intégrité complète des données.

---

## Requêtes SQL de Contrôle

### 1. Vérification du Volume de Données

```sql
-- Comparer le nombre d'enregistrements
SELECT 
    'Source (Novaprint)' AS Base,
    COUNT(*) AS Nombre_Lignes
FROM Novaprint.dbo.PAPIERS_IMPRIMEURS
UNION ALL
SELECT 
    'Cible (novaprint_restored)' AS Base,
    COUNT(*) AS Nombre_Lignes
FROM novaprint_restored.dbo.PAPIERS_IMPRIMEURS;

-- Résultat attendu : 
-- - Les enregistrements présents dans la source doivent exister en cible
-- - Des enregistrements supplémentaires en cible sont acceptables s'ils ne sont pas référencés
```

**Critère de validation** : ✅ Tous les enregistrements de la source existent en cible

---

### 2. Vérification de la Correspondance des IDs

```sql
-- Comparer les IDs pour les enregistrements correspondants
USE novaprint_restored;

SELECT COUNT(*) AS mismatches
FROM novaprint_restored.dbo.PAPIERS_IMPRIMEURS cible
INNER JOIN Novaprint.dbo.PAPIERS_IMPRIMEURS source
    ON cible.ID_PAPIER = source.ID_PAPIER
    AND cible.ID_IMPRIMEUR = source.ID_IMPRIMEUR
WHERE cible.ID <> source.ID;

-- Résultat attendu : 0 lignes (tous les IDs correspondent)
```

**Critère de validation** : ✅ Aucun mismatch d'ID pour les enregistrements correspondants

---

### 3. Vérification des Clés Étrangères Entrantes - PAPIERS_TARIF_FMT

```sql
-- Vérifier les références vers PAPIERS_IMPRIMEURS dans PAPIERS_TARIF_FMT
USE novaprint_restored;

SELECT 
    'PAPIERS_TARIF_FMT' AS Table_Referencee,
    COUNT(*) AS Total_References,
    COUNT(DISTINCT ptf.ID_PAPIMPRIM) AS References_Distinctes,
    COUNT(CASE WHEN pi.ID IS NULL THEN 1 END) AS References_Orphelines,
    COUNT(CASE WHEN pi.ID IS NOT NULL THEN 1 END) AS References_Valides
FROM PAPIERS_TARIF_FMT ptf
LEFT JOIN PAPIERS_IMPRIMEURS pi ON ptf.ID_PAPIMPRIM = pi.ID
WHERE ptf.ID_PAPIMPRIM IS NOT NULL;

-- Résultat attendu : References_Orphelines = 0 (ou égal au nombre avant réalignement)
```

**Critère de validation** : ✅ Aucune nouvelle référence orpheline créée par le réalignement

---

### 4. Vérification des Clés Étrangères Entrantes - PAPIERS_TARIF_GRAM

```sql
-- Vérifier les références vers PAPIERS_IMPRIMEURS dans PAPIERS_TARIF_GRAM
USE novaprint_restored;

SELECT 
    'PAPIERS_TARIF_GRAM' AS Table_Referencee,
    COUNT(*) AS Total_References,
    COUNT(DISTINCT ptg.ID_PAPIMPRIM) AS References_Distinctes,
    COUNT(CASE WHEN pi.ID IS NULL THEN 1 END) AS References_Orphelines,
    COUNT(CASE WHEN pi.ID IS NOT NULL THEN 1 END) AS References_Valides
FROM PAPIERS_TARIF_GRAM ptg
LEFT JOIN PAPIERS_IMPRIMEURS pi ON ptg.ID_PAPIMPRIM = pi.ID
WHERE ptg.ID_PAPIMPRIM IS NOT NULL;

-- Résultat attendu : References_Orphelines = 0 (ou égal au nombre avant réalignement)
```

**Critère de validation** : ✅ Aucune nouvelle référence orpheline créée par le réalignement

---

### 5. Vérification des Clés Étrangères Sortantes

```sql
-- Vérifier les références depuis PAPIERS_IMPRIMEURS
USE novaprint_restored;

-- Vers IMPRIMEURS
SELECT 
    'IMPRIMEURS' AS Table_Referencee,
    COUNT(*) AS Total_References,
    COUNT(CASE WHEN i.ID_SOCIETE IS NULL THEN 1 END) AS References_Orphelines,
    COUNT(CASE WHEN i.ID_SOCIETE IS NOT NULL THEN 1 END) AS References_Valides
FROM PAPIERS_IMPRIMEURS pi
LEFT JOIN IMPRIMEURS i ON pi.ID_IMPRIMEUR = i.ID_SOCIETE
WHERE pi.ID_IMPRIMEUR IS NOT NULL;

-- Vers PAPIERS
SELECT 
    'PAPIERS' AS Table_Referencee,
    COUNT(*) AS Total_References,
    COUNT(CASE WHEN p.ID IS NULL THEN 1 END) AS References_Orphelines,
    COUNT(CASE WHEN p.ID IS NOT NULL THEN 1 END) AS References_Valides
FROM PAPIERS_IMPRIMEURS pi
LEFT JOIN PAPIERS p ON pi.ID_PAPIER = p.ID
WHERE pi.ID_PAPIER IS NOT NULL;

-- Résultat attendu : References_Orphelines = 0 pour chaque table
```

**Critère de validation** : ✅ Toutes les FK sortantes sont valides

---

### 6. Vérification de l'Absence de Duplication

```sql
-- Vérifier les IDs dupliqués
USE novaprint_restored;

SELECT COUNT(*) AS IDs_Dupliques
FROM (
    SELECT ID, COUNT(*) AS cnt 
    FROM PAPIERS_IMPRIMEURS 
    GROUP BY ID 
    HAVING COUNT(*) > 1
) AS dup;

-- Résultat attendu : 0
```

**Critère de validation** : ✅ Aucun ID dupliqué

---

### 7. Vérification de la Validité des Index

```sql
-- Vérifier l'état des index
USE novaprint_restored;

SELECT 
    i.name AS index_name,
    i.is_primary_key,
    i.is_unique,
    i.is_disabled,
    CASE WHEN i.is_disabled = 0 THEN 'ACTIF' ELSE 'DESACTIVE' END AS statut
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name = 'PAPIERS_IMPRIMEURS'
AND i.name IS NOT NULL
ORDER BY i.is_primary_key DESC, i.name;

-- Résultat attendu : Tous les index sont actifs (is_disabled = 0)
```

**Critère de validation** : ✅ Tous les index sont actifs et valides

---

### 8. Vérification de la Cohérence des Tables Liées

```sql
-- Vérifier que les références dans PAPIERS_TARIF_FMT pointent vers les bons IDs
USE novaprint_restored;

SELECT COUNT(*) AS references_incoherentes
FROM PAPIERS_TARIF_FMT ptf
INNER JOIN PAPIERS_IMPRIMEURS pi ON ptf.ID_PAPIMPRIM = pi.ID
INNER JOIN Novaprint.dbo.PAPIERS_IMPRIMEURS pi_source 
    ON pi.ID_PAPIER = pi_source.ID_PAPIER
    AND pi.ID_IMPRIMEUR = pi_source.ID_IMPRIMEUR
WHERE pi.ID <> pi_source.ID;

-- Vérifier que les références dans PAPIERS_TARIF_GRAM pointent vers les bons IDs
SELECT COUNT(*) AS references_incoherentes
FROM PAPIERS_TARIF_GRAM ptg
INNER JOIN PAPIERS_IMPRIMEURS pi ON ptg.ID_PAPIMPRIM = pi.ID
INNER JOIN Novaprint.dbo.PAPIERS_IMPRIMEURS pi_source 
    ON pi.ID_PAPIER = pi_source.ID_PAPIER
    AND pi.ID_IMPRIMEUR = pi_source.ID_IMPRIMEUR
WHERE pi.ID <> pi_source.ID;

-- Résultat attendu : 0 pour chaque requête
```

**Critère de validation** : ✅ Toutes les références sont cohérentes

---

## Vérification Automatique

### Exécution du Script Python

```bash
python projet21_verification_integrite_papiers_imprimeurs.py
```

Le script effectue automatiquement toutes les vérifications ci-dessus et génère un rapport JSON détaillé.

---

## Critères de Validation Globale

### ✅ Alignement SÛR si :

1. **Volume de données** : Tous les enregistrements de la source existent en cible
2. **Correspondance des IDs** : Tous les IDs correspondent pour les enregistrements alignés
3. **FK Entrantes** : Aucune nouvelle référence orpheline créée
   - PAPIERS_TARIF_FMT : Références valides
   - PAPIERS_TARIF_GRAM : Références valides
4. **FK Sortantes** : Toutes valides
   - Vers IMPRIMEURS : Toutes valides
   - Vers PAPIERS : Toutes valides
5. **Absence de duplication** : Aucun ID dupliqué, aucune donnée dupliquée
6. **Index** : Tous les index sont actifs et valides
7. **Cohérence** : Toutes les références dans les tables liées sont cohérentes

### ⚠️ Alignement avec ATTENTION si :

- Des références orphelines existent mais étaient présentes avant le réalignement
- Des enregistrements supplémentaires existent en cible (non présents en source)

### ❌ Alignement NON SÛR si :

- Perte d'enregistrements
- IDs ne correspondent pas après réalignement
- Nouvelles références orphelines créées
- Duplications détectées
- Index désactivés ou invalides

---

## Actions Recommandées après Vérification

### Si l'alignement est SÛR :

1. **Réactiver la confiance des contraintes** (si nécessaire) :
   ```sql
   ALTER TABLE PAPIERS_TARIF_FMT 
   WITH CHECK CHECK CONSTRAINT FK__PAPIERS_T__ID_PA__49659AB2;
   
   ALTER TABLE PAPIERS_TARIF_GRAM 
   WITH CHECK CHECK CONSTRAINT FK__PAPIERS_T__ID_PA__4A59BEEB;
   ```

2. **Documenter le résultat** : Conserver le rapport de vérification

### Si des références orphelines existent :

- **Analyser leur origine** : Vérifier si elles existaient avant le réalignement
- **Décider de leur traitement** : Les corriger ou les documenter comme données historiques

---

**Document généré automatiquement**  
**Script de vérification** : `projet21_verification_integrite_papiers_imprimeurs.py`
