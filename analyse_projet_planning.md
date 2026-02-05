# Analyse du Projet Planning & Suivi des Délais de Livraison

## 1. Identification du Projet

**Nom actuel :** Planning  
**Nom proposé :** Planning & Suivi des Délais de Livraison  
**Code Projet :** Projet 1  
**Fichiers principaux :**
- `logic/projet1.py` - Logique backend
- `templates/projet1.html` - Interface utilisateur
- Routes : `/projet1/` et `/projet1/api/*`

---

## 2. Source des Données

### 2.1 Numéro de Dossier

**Source principale :** Table `COMMANDES`  
**Colonne :** `COMMANDES.Numero`  
**Type :** Identifiant unique de la commande/dossier

**Requête SQL utilisée :**
```sql
SELECT C.Numero, C.DteLivPrev, C.Reference, S.RaiSocTri AS Client
FROM COMMANDES C
LEFT JOIN SOCIETES S ON C.ID_SOCIETE = S.ID
WHERE C.Termine = 0 AND C.EtatLiv = 0
```

**Filtres appliqués :**
- `Termine = 0` : Seules les commandes non terminées
- `EtatLiv = 0` : Seules les commandes non livrées

### 2.2 Date de Livraison Prévue

**Colonne :** `COMMANDES.DteLivPrev`  
**Type :** DATE  
**Usage :** Date affichée dans le calendrier comme date de début (`start`) de l'événement

### 2.3 Informations Complémentaires

- **Client :** `SOCIETES.RaiSocTri` (via jointure LEFT JOIN)
- **Référence :** `COMMANDES.Reference`
- **Statut :** Basé sur `COMMANDES.Termine` et `COMMANDES.EtatLiv`

---

## 3. Flux Fonctionnel et Technique

### 3.1 Chargement Initial des Données

**Flux :**
1. Page chargée → `projet1.html`
2. JavaScript exécute : `fetch('/projet1/api/commandes')`
3. Route backend : `@bp.route("/api/commandes")` dans `logic/projet1.py`
4. Fonction appelée : `get_commandes()` dans `db.py`
5. Requête SQL exécutée sur `COMMANDES`
6. Données formatées pour FullCalendar :
   ```javascript
   {
     "id": numero,
     "title": numero,
     "start": DteLivPrev (format YYYY-MM-DD),
     "reference": Reference,
     "client": Client
   }
   ```
7. Affichage dans le calendrier FullCalendar

### 3.2 Déplacement d'un Dossier (Drag & Drop)

**État actuel :** ⚠️ **NON IMPLÉMENTÉ**

**Observation :**
- Le calendrier a `editable: true` dans la configuration FullCalendar
- **MAIS** aucun gestionnaire d'événement `eventDrop` ou `eventChange` n'est présent dans le code JavaScript
- La route `/projet1/update_commande` existe dans le backend mais n'est pas appelée depuis le frontend

**Ce qui devrait se passer (si implémenté) :**

1. **Côté Client (JavaScript) :**
   ```javascript
   eventDrop: function(info) {
       // Récupérer le nouveau numéro et la nouvelle date
       const numero = info.event.id;
       const newDate = info.event.startStr;
       
       // Appel API
       fetch('/projet1/update_commande', {
           method: 'POST',
           headers: {'Content-Type': 'application/json'},
           body: JSON.stringify({
               id: numero,
               start: newDate
           })
       })
   }
   ```

2. **Côté Serveur (Python) :**
   - Route : `@bp.route("/update_commande", methods=["POST"])`
   - Fonction : `update_commande(numero, new_date, user=None)` dans `db.py`

---

## 4. Impact sur la Base de Données

### 4.1 Table COMMANDES (Table Source)

**Colonne modifiée lors du déplacement :**
- `COMMANDES.DteLivPrev` → Mise à jour directe avec la nouvelle date

**Requête SQL exécutée :**
```sql
UPDATE COMMANDES 
SET DteLivPrev = ? 
WHERE Numero = ?
```

**Impact :**
- ✅ **Modification directe** de la table source `COMMANDES`
- ✅ La date prévue de livraison est **immédiatement mise à jour**
- ⚠️ **Pas de sauvegarde automatique** de l'ancienne valeur dans `COMMANDES` (sauf si historique activé)

### 4.2 Table HISTORIQUE_LIVRAISON (Table de Traçabilité)

**Structure identifiée :**
- `ID` : Clé primaire auto-incrémentée
- `NumeroCommande` : Numéro de la commande (FK vers COMMANDES.Numero)
- `AncienneDate` : Date avant modification (DATE)
- `NouvelleDate` : Date après modification (DATE)
- `ModifiePar` : Utilisateur ayant effectué la modification (VARCHAR)
- `DateModification` : Timestamp de la modification (DATETIME, probablement auto-généré)

### 4.3 Table LIVRAISONS_CMDE (Table de Dates Réelles)

**Structure identifiée :**
- `ID` : Clé primaire
- `ID_COMMANDE` : Clé étrangère vers COMMANDES.ID
- `DteLiv` : Date réelle de livraison (DATE)

**Usage :**
- Utilisée pour comparer la date prévue (`COMMANDES.DteLivPrev`) avec la date réelle (`LIVRAISONS_CMDE.DteLiv`)
- Permet de calculer les écarts et les statistiques de ponctualité

**Insertion conditionnelle :**
```sql
INSERT INTO HISTORIQUE_LIVRAISON 
(NumeroCommande, AncienneDate, NouvelleDate, ModifiePar)
VALUES (?, ?, ?, ?)
```

**Condition d'insertion :**
- ✅ Insertion **uniquement si** `user` est fourni (paramètre optionnel)
- ⚠️ Si `user=None`, **aucun historique n'est enregistré**

**Problème identifié :**
- Le paramètre `user` n'est **jamais transmis** depuis le frontend dans la route actuelle
- L'historique ne sera **jamais créé** avec l'implémentation actuelle

---

## 5. Schéma Logique des Tables

```
┌─────────────────────────────────┐
│         COMMANDES               │
├─────────────────────────────────┤
│ PK: ID                          │
│     Numero (UNIQUE)             │
│     DteLivPrev (DATE) ◄─────────┼─── MODIFIÉE LORS DU DÉPLACEMENT
│     Reference                    │
│     ID_SOCIETE (FK)             │
│     Termine (BIT)               │
│     EtatLiv (BIT)               │
└─────────────────────────────────┘
         │
         │ (1:N)
         │
         ▼
┌─────────────────────────────────┐
│    HISTORIQUE_LIVRAISON         │
├─────────────────────────────────┤
│ PK: ID (auto-incrémenté)        │
│ FK: NumeroCommande              │
│     AncienneDate (DATE)         │
│     NouvelleDate (DATE)         │
│     ModifiePar (VARCHAR)        │
│     DateModification (DATETIME) │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│         SOCIETES                │
├─────────────────────────────────┤
│ PK: ID                          │
│     RaiSocTri (VARCHAR)         │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│      LIVRAISONS_CMDE            │
├─────────────────────────────────┤
│ PK: ID                          │
│ FK: ID_COMMANDE → COMMANDES.ID  │
│     DteLiv (DATE)               │
└─────────────────────────────────┘
```

---

## 6. Règles de Gestion Associées au Déplacement

### 6.1 Règles Actuelles (dans le code)

1. **Validation :**
   - ✅ Vérification que le numéro existe dans `COMMANDES`
   - ✅ Récupération de l'ancienne date avant modification
   - ✅ Conversion de la date au format DATE SQL Server

2. **Mise à jour :**
   - ✅ Mise à jour directe de `COMMANDES.DteLivPrev`
   - ✅ Transaction avec commit explicite

3. **Historique :**
   - ⚠️ Création d'un enregistrement dans `HISTORIQUE_LIVRAISON` **uniquement si** `user` est fourni
   - ⚠️ **Problème :** `user` n'est jamais transmis depuis le frontend

### 6.2 Règles Manquantes ou à Améliorer

1. **Traçabilité :**
   - ❌ Pas d'enregistrement systématique de l'utilisateur
   - ❌ Pas de timestamp de modification dans `COMMANDES` (si colonne existe)

2. **Validation métier :**
   - ❌ Pas de validation de la nouvelle date (ex: date dans le futur/passé)
   - ❌ Pas de vérification des droits d'accès
   - ❌ Pas de notification aux parties prenantes

3. **Cohérence :**
   - ⚠️ Pas de vérification de cohérence avec d'autres tables (ex: `WEB_TRAITEMENTS`)
   - ⚠️ Pas de synchronisation avec d'autres modules

---

## 7. Recommandations

### 7.1 Corrections Immédiates

#### A. Implémenter le gestionnaire d'événement FullCalendar

**Fichier :** `templates/projet1.html`

**Ajouter dans la configuration de `calStd` :**
```javascript
calStd = new FullCalendar.Calendar(document.getElementById('calendarStandard'), {
    // ... configuration existante ...
    editable: true,
    eventDrop: function(info) {
        const numero = info.event.id;
        const newDate = info.event.startStr;
        
        fetch('/projet1/update_commande', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                id: numero,
                start: newDate,
                user: '{{ get_current_user() }}' // À adapter selon votre système d'auth
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Date mise à jour avec succès');
            } else {
                info.revert(); // Annuler le déplacement en cas d'erreur
                alert('Erreur lors de la mise à jour');
            }
        })
        .catch(error => {
            info.revert();
            console.error('Erreur:', error);
        });
    }
});
```

#### B. Transmettre l'utilisateur depuis le frontend

**Modifier la route backend :**
```python
@bp.route("/update_commande", methods=["POST"])
def api_update_commande():
    data = request.get_json()
    numero = data.get("id")
    new_date = data.get("start")
    user = data.get("user") or session.get('matricule') or 'System'  # Récupérer depuis la session
    
    if numero and new_date:
        success = update_commande(numero, new_date, user)
        # ...
```

### 7.2 Améliorations Structurelles

#### A. Créer une table dédiée au planning (optionnel)

**Avantages :**
- Séparation des préoccupations
- Possibilité de gérer plusieurs versions de planning
- Pas de modification directe de `COMMANDES`

**Structure proposée :**
```sql
CREATE TABLE WEB_PLANNING (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    NumeroCommande VARCHAR(50) NOT NULL,
    DatePrevue DATE NOT NULL,
    DateModification DATETIME DEFAULT GETDATE(),
    ModifiePar VARCHAR(50),
    FOREIGN KEY (NumeroCommande) REFERENCES COMMANDES(Numero)
)
```

**Inconvénients :**
- Nécessite une synchronisation avec `COMMANDES`
- Complexité accrue

**Recommandation :** ⚠️ **Ne pas créer** si la modification directe de `COMMANDES.DteLivPrev` est acceptable métier

#### B. Améliorer la traçabilité

**Modifier `update_commande` pour toujours créer un historique :**
```python
def update_commande(numero, new_date, user='System'):
    # ... code existant ...
    # Toujours créer un historique, même si user n'est pas fourni
    cursor.execute("""
        INSERT INTO HISTORIQUE_LIVRAISON 
        (NumeroCommande, AncienneDate, NouvelleDate, ModifiePar)
        VALUES (?, ?, ?, ?)
    """, numero, old_date, new_date_obj, user or 'System')
```

#### C. Ajouter des validations métier

**Dans `update_commande` :**
```python
# Validation : date ne peut pas être dans le passé de plus de X jours
# Validation : vérifier les droits d'accès
# Validation : vérifier la cohérence avec d'autres modules
```

### 7.3 Synchronisation avec Autres Modules

**Vérifier l'impact sur :**
- `WEB_TRAITEMENTS` : Si cette table référence `COMMANDES.DteLivPrev`
- Autres projets utilisant `COMMANDES.DteLivPrev`

**Recommandation :** Documenter les dépendances et créer des triggers SQL si nécessaire

---

## 8. Routes API Manquantes

### 8.1 Routes Appelées dans le Template mais Non Implémentées

Le template `projet1.html` appelle plusieurs routes API qui **n'existent pas** dans `logic/projet1.py` :

1. ❌ `/projet1/api/commandes-avec-suivi`
   - **Fonction backend disponible :** `get_commandes_avec_suivi()` dans `db.py`
   - **Action requise :** Ajouter la route dans `logic/projet1.py`

2. ❌ `/projet1/api/alertes-retard`
   - **Fonction backend disponible :** `get_alertes_retard()` dans `db.py`
   - **Action requise :** Ajouter la route dans `logic/projet1.py`

3. ❌ `/projet1/api/statistiques-performance`
   - **Fonction backend disponible :** `get_statistiques_performance()` dans `db.py`
   - **Action requise :** Ajouter la route dans `logic/projet1.py`

4. ❌ `/projet1/api/performance-par-client`
   - **Fonction backend disponible :** `get_performance_par_client()` dans `db.py`
   - **Action requise :** Ajouter la route dans `logic/projet1.py`

5. ❌ `/projet1/api/marquer-livraison`
   - **Fonction backend disponible :** `marquer_livraison()` dans `db.py`
   - **Action requise :** Ajouter la route dans `logic/projet1.py`

**Impact :** Les onglets "Suivi des Délais" et "Performance" ne fonctionnent pas correctement car les données ne peuvent pas être chargées.

---

## 9. Conclusion

### 9.1 État Actuel

✅ **Fonctionnel :**
- Chargement des données depuis `COMMANDES`
- Affichage dans le calendrier FullCalendar
- Route backend prête pour la mise à jour

❌ **Non fonctionnel :**
- Déplacement drag & drop non implémenté côté client
- Historique non créé (paramètre `user` manquant)

### 9.2 Impact du Déplacement

**Réponse à la question principale :**

> Le déplacement d'un dossier met-il à jour directement la table source `COMMANDES` ?

**Réponse :** ✅ **OUI**, avec l'implémentation actuelle :
- La fonction `update_commande()` modifie **directement** `COMMANDES.DteLivPrev`
- **Aucune table dédiée** au planning n'est utilisée
- Une table d'historique (`HISTORIQUE_LIVRAISON`) existe mais n'est **pas systématiquement alimentée**

### 9.3 Risques Identifiés

1. **Désynchronisation :**
   - Modification directe sans validation métier
   - Pas de vérification de cohérence avec d'autres modules

2. **Traçabilité incomplète :**
   - Historique non systématique
   - Pas d'identification de l'utilisateur

3. **Fonctionnalité incomplète :**
   - Drag & drop non fonctionnel (code manquant)

### 9.4 Actions Recommandées

1. **Court terme :**
   - ✅ Implémenter le gestionnaire `eventDrop` dans FullCalendar
   - ✅ Transmettre l'utilisateur depuis la session Flask
   - ✅ Renommer le projet dans `WEB_PROJETS`

2. **Moyen terme :**
   - ✅ Améliorer la traçabilité (historique systématique)
   - ✅ Ajouter des validations métier
   - ✅ Documenter les dépendances

3. **Long terme (optionnel) :**
   - ⚠️ Créer une table dédiée au planning si besoin de versions multiples
   - ⚠️ Implémenter des notifications automatiques

---

## 10. Schéma de Flux Complet (Recommandé)

```
┌─────────────────────────────────────────────────────────┐
│                    UTILISATEUR                          │
│              (Drag & Drop sur calendrier)               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              FRONTEND (projet1.html)                    │
│  - FullCalendar eventDrop                               │
│  - fetch('/projet1/update_commande')                    │
└────────────────────┬────────────────────────────────────┘
                     │ POST {id, start, user}
                     ▼
┌─────────────────────────────────────────────────────────┐
│           BACKEND (logic/projet1.py)                    │
│  - Route: /update_commande                              │
│  - Validation des données                                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              DATABASE (db.py)                          │
│  1. SELECT ancienne date (COMMANDES)                    │
│  2. UPDATE COMMANDES.DteLivPrev                         │
│  3. INSERT HISTORIQUE_LIVRAISON                          │
│  4. COMMIT transaction                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              TABLES MODIFIÉES                           │
│  ✅ COMMANDES.DteLivPrev (modifiée)                     │
│  ✅ HISTORIQUE_LIVRAISON (nouvelle ligne)                │
└─────────────────────────────────────────────────────────┘
```

---

---

## 11. Résumé Exécutif

### 11.1 Réponses aux Questions Principales

#### Q1 : Quelle est l'origine du numéro de dossier ?
**R :** Le numéro de dossier provient de `COMMANDES.Numero` (table source principale)

#### Q2 : Comment le numéro de dossier est-il chargé et utilisé ?
**R :** 
- Chargement via API `/projet1/api/commandes` → fonction `get_commandes()` dans `db.py`
- Affichage dans le calendrier FullCalendar comme identifiant (`id`) et titre (`title`)
- Format : Chaîne de caractères (ex: "2025120177")

#### Q3 : Le déplacement met-il à jour directement COMMANDES ?
**R :** ✅ **OUI**
- Modification directe de `COMMANDES.DteLivPrev`
- Aucune table dédiée au planning n'est utilisée
- Table d'historique (`HISTORIQUE_LIVRAISON`) existe mais n'est pas systématiquement alimentée

#### Q4 : Y a-t-il une table dédiée au planning ?
**R :** ❌ **NON**
- Pas de table `WEB_PLANNING` ou équivalent
- Modification directe de la table source `COMMANDES`

### 11.2 Structure des Tables Impliquées

| Table | Colonne Modifiée | Type Modification | Fréquence |
|-------|-----------------|-------------------|-----------|
| `COMMANDES` | `DteLivPrev` | UPDATE direct | À chaque déplacement |
| `HISTORIQUE_LIVRAISON` | Nouvelle ligne | INSERT | Conditionnel (si user fourni) |
| `LIVRAISONS_CMDE` | `DteLiv` | Aucune (lecture seule) | - |

### 11.3 État de Fonctionnalité

| Fonctionnalité | État | Commentaire |
|----------------|------|-------------|
| Affichage calendrier | ✅ Fonctionnel | Données chargées depuis COMMANDES |
| Déplacement drag & drop | ❌ Non implémenté | Code JavaScript manquant |
| Mise à jour backend | ✅ Prêt | Route existe mais non appelée |
| Historique | ⚠️ Partiel | Créé uniquement si user fourni |
| Suivi des délais | ❌ Non fonctionnel | Routes API manquantes |
| Performance | ❌ Non fonctionnel | Routes API manquantes |

### 11.4 Actions Prioritaires

1. **URGENT :** Implémenter le gestionnaire `eventDrop` dans FullCalendar
2. **URGENT :** Ajouter les routes API manquantes dans `logic/projet1.py`
3. **IMPORTANT :** Transmettre l'utilisateur depuis la session Flask
4. **IMPORTANT :** Renommer le projet dans `WEB_PROJETS`
5. **RECOMMANDÉ :** Améliorer la traçabilité (historique systématique)

---

**Date d'analyse :** 2026-01-29  
**Version du document :** 1.0  
**Auteur :** Analyse automatique du codebase
