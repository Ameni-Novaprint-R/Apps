# Test d'enregistrement des valeurs dans WEB_S_DOS_ENCOURS

## Règles à respecter

### 1️⃣ Colonne QteComm_COMMANDES
- ✅ DOIT enregistrer la valeur de la ligne de saisie (préremplie ou modifiée)
- ✅ DOIT enregistrer la valeur modifiée dans une ligne existante
- ❌ NE DOIT PAS utiliser la valeur de COMMANDES.QteComm

### 2️⃣ Colonne PrixVenteTotal
- ✅ DOIT enregistrer la valeur AFFICHÉE dans l'application
- ✅ DOIT être calculée côté client : PrixVenteTotal = PrixVenteUnitaire × Quantité
- ❌ NE DOIT PAS être recalculée côté serveur

### 3️⃣ Règle d'enregistrement
- ✅ Les valeurs AFFICHÉES dans l'application sont celles enregistrées
- ❌ Aucune formule dans la base de données
- ❌ Aucune logique métier dans la table
- ✅ La base = stockage fidèle des valeurs de l'application

## Points de vérification dans le code

### Backend (db.py)

#### `create_web_s_dos_encours()`
- ✅ Ligne 1821 : `values = [numero.strip(), client, reference, quantite, marge]`
  - `quantite` vient du paramètre (valeur de l'application)
- ✅ Ligne 1816 : `values.append(prix_vente_total)`
  - `prix_vente_total` vient du paramètre (valeur calculée côté client)

#### `update_web_s_dos_encours_quantite()`
- ✅ Ligne 1663 : `SET QteComm_COMMANDES = ?` avec `nouvelle_quantite`
  - `nouvelle_quantite` vient du paramètre (valeur de l'application)
- ✅ Ligne 1664 : `SET PrixVenteTotal = ?` avec `prix_vente_total`
  - `prix_vente_total` vient du paramètre (valeur calculée côté client)

### API (routes/projet19_routes.py)

#### `api_create_dossier()`
- ✅ Ligne 171 : `quantite=quantite_saisie`
  - `quantite_saisie` vient de `data.get('quantite')` (valeur de l'application)
- ✅ Ligne 177 : `prix_vente_total=prix_vente_total`
  - `prix_vente_total` vient de `data.get('prix_vente_total')` (valeur calculée côté client)

#### `api_update_quantite()`
- ✅ Ligne 220 : `update_web_s_dos_encours_quantite(dossier_id, nouvelle_quantite, prix_vente_total=prix_vente_total)`
  - `nouvelle_quantite` vient de `data.get('quantite')` (valeur de l'application)
  - `prix_vente_total` vient de `data.get('prix_vente_total')` (valeur calculée côté client)

### Frontend (templates/projet19.html)

#### `saveNewDossier()`
- ✅ Récupère `prixVenteTotal` depuis `#input-prix-vente-total`
- ✅ Ajoute `prix_vente_total` au payload

#### `saveEdit()`
- ✅ Récupère `prixVenteTotal` depuis `.edit-prix-total-display`
- ✅ Transmet à `updateQuantite(id, quantite, prixVenteTotal)`

#### `updateQuantite()`
- ✅ Accepte `prixVenteTotal` en paramètre
- ✅ Ajoute `prix_vente_total` au payload

## Tests à effectuer

1. **Création d'un nouveau dossier**
   - Saisir un numéro de dossier
   - Modifier la quantité (ex: 1000 → 1500)
   - Vérifier que le prix total se met à jour en temps réel
   - Enregistrer
   - Vérifier dans la DB : `QteComm_COMMANDES = 1500` et `PrixVenteTotal` = valeur affichée

2. **Modification d'une ligne existante**
   - Cliquer sur "Modifier"
   - Modifier la quantité (ex: 500 → 1500)
   - Vérifier que le prix total se met à jour en temps réel
   - Enregistrer
   - Vérifier dans la DB : `QteComm_COMMANDES = 1500` et `PrixVenteTotal` = valeur affichée
