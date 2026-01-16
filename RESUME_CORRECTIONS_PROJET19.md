# Résumé des Corrections - Projet 19

## ✅ Corrections appliquées

### 1. Table WEB_S_DOS_ENCOURS vide par défaut
- ✅ **1458 lignes supprimées** de la table WEB_S_DOS_ENCOURS
- ✅ Script de création modifié pour ne plus insérer automatiquement les données
- ✅ La table reste vide jusqu'à ce qu'un utilisateur ajoute explicitement un dossier

### 2. Recherche dans COMMANDES (lecture seule)
- ✅ Nouvelle fonction `search_commandes_by_numero()` dans `db.py`
- ✅ Nouvelle fonction `get_commande_by_numero()` dans `db.py`
- ✅ Routes API séparées :
  - `/api/search-commandes` : Recherche dans COMMANDES (lecture seule)
  - `/api/search-dossiers` : Recherche dans WEB_S_DOS_ENCOURS
  - `/api/commande/<numero>` : Récupère une commande depuis COMMANDES

### 3. Interface utilisateur réorganisée
- ✅ **Deux onglets distincts** :
  1. **🔍 Rechercher une commande** : Recherche dans COMMANDES (lecture seule)
  2. **📁 Dossiers en suivi** : Affiche les dossiers déjà dans WEB_S_DOS_ENCOURS

### 4. Ajout explicite au suivi
- ✅ Bouton **"➕ Ajouter au suivi"** sur chaque commande trouvée
- ✅ L'enregistrement dans WEB_S_DOS_ENCOURS se fait **uniquement après clic** sur ce bouton
- ✅ Aucune création automatique lors de la recherche

### 5. Règles de sécurité respectées
- ✅ **COMMANDES et SOCIETES** : Strictement en lecture seule
- ✅ **WEB_S_DOS_ENCOURS** : Seule table modifiable (CRUD)
- ✅ Toutes les opérations CRUD concernent exclusivement WEB_S_DOS_ENCOURS

## Fonctionnement actuel

### Onglet 1 : Rechercher une commande
1. L'utilisateur saisit un numéro de dossier (recherche "contient")
2. La recherche se fait dans **COMMANDES** (lecture seule)
3. Les résultats affichent : Numéro, Client, Désignation, Quantité, Marge
4. Chaque résultat a un bouton **"➕ Ajouter au suivi"**
5. **Aucune ligne n'est créée automatiquement** dans WEB_S_DOS_ENCOURS

### Onglet 2 : Dossiers en suivi
1. Affiche les dossiers déjà dans WEB_S_DOS_ENCOURS
2. Permet de modifier la quantité (seul champ modifiable)
3. Permet de retirer un dossier du suivi (suppression)

### Processus d'ajout au suivi
1. Recherche dans COMMANDES → Sélection d'une commande
2. Clic sur **"➕ Ajouter au suivi"**
3. Les données sont copiées depuis COMMANDES vers WEB_S_DOS_ENCOURS
4. Le dossier apparaît dans l'onglet "Dossiers en suivi"

## Fichiers modifiés

1. **`db.py`** :
   - Ajout de `search_commandes_by_numero()` (lecture seule)
   - Ajout de `get_commande_by_numero()` (lecture seule)

2. **`routes/projet19_routes.py`** :
   - Nouvelle route `/api/search-commandes` (recherche dans COMMANDES)
   - Nouvelle route `/api/commande/<numero>` (récupération depuis COMMANDES)
   - Route `/api/search-dossiers` séparée (recherche dans WEB_S_DOS_ENCOURS)

3. **`templates/projet19.html`** :
   - Interface complètement réécrite avec deux onglets
   - Bouton explicite "Ajouter au suivi"
   - Séparation claire entre recherche et gestion

4. **`create_web_s_dos_encours.py`** :
   - Ne copie plus automatiquement les données
   - La table est créée vide

5. **`vider_web_s_dos_encours.py`** (nouveau) :
   - Script pour vider la table si nécessaire

## État actuel

- ✅ Table WEB_S_DOS_ENCOURS : **0 lignes** (vide)
- ✅ Recherche dans COMMANDES : **Fonctionnelle** (lecture seule)
- ✅ Ajout explicite au suivi : **Fonctionnel**
- ✅ Modification de quantité : **Fonctionnelle**
- ✅ Suppression de dossier : **Fonctionnelle**

## Prochaines étapes

1. Redémarrer Flask pour charger les nouvelles routes
2. Tester l'interface avec une recherche dans COMMANDES
3. Tester l'ajout explicite d'un dossier au suivi
4. Vérifier que COMMANDES et SOCIETES restent inchangées




