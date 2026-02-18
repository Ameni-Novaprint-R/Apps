# Analyse du Projet 5 - Suivi Production (prinects)

## Vue d'ensemble

Le **Projet 5** est une application Flask de suivi de production qui permet de gérer les fiches de travail, les traitements, les opérations et les opérateurs dans un contexte industriel. L'application est hébergée sur le serveur `\\prinects\Apps`.

## Structure des fichiers

### Backend (Python/Flask)

**Fichier principal :** `\\prinects\Apps\logic\projet5.py`

- **Blueprint Flask :** `/projet5`
- **Nombre de routes :** ~30+ routes API et pages
- **Lignes de code :** ~2100 lignes

### Frontend (HTML/JavaScript)

**Fichier principal :** `\\prinects\Apps\templates\projet5.html`

- **Framework :** Bootstrap 5, jQuery, DataTables, Chart.js
- **Lignes de code :** ~2400 lignes
- **Interface :** Multi-onglets avec plusieurs sections

## Fonctionnalités principales

### 1. Gestion des fiches de travail

#### Routes principales :
- `GET /projet5/` - Page principale
- `GET /projet5/api/fiche_travail` - Liste des fiches de travail
- `GET /projet5/api/fiches_filtrees` - Fiches filtrées par service/poste/état
- `POST /projet5/api/save_traitement` - Enregistrer un traitement

#### Tables de base de données :
- `GP_FICHES_TRAVAIL` - Fiches de travail principales
- `GP_TRAITEMENTS` - Traitements (sessions de production)
- `GP_FICHES_OPERATIONS` - Opérations liées aux fiches
- `GP_POSTES` - Postes de travail (machines)
- `GP_SERVICES` - Services de production
- `GP_POSTES_OP` - Opérations disponibles par poste
- `COMMANDES` - Commandes clients
- `SOCIETES` - Clients
- `PERSONNES` - Opérateurs
- `EMPLOYES` - Employés (liés aux personnes)
- `GP_FICHTRA_INT` - Informations internes des fiches

### 2. Gestion des sessions de production

#### Routes :
- `POST /projet5/api/set_debut` - Démarrer une session
- `POST /projet5/api/set_fin` - Terminer une session
- `POST /projet5/api/set_interrompu` - Interrompre une session
- `POST /projet5/api/reprendre` - Reprendre une session interrompue
- `GET /projet5/api/historique_sessions/<id_fiche>` - Historique des sessions

#### États des fiches (CodIndAv) :
- `0` : Bloqué (opération précédente non terminée)
- `1` : Prêt à commencer
- `2` : En cours ou interrompue
- `3` : Terminé
- `4` : Terminé et facturé

### 3. Filtrage et recherche

#### Filtres disponibles :
- **Par service** : Filtrage par service de production
- **Par poste/machine** : Filtrage par machine spécifique
- **Par état** : Non débuté, En cours, Terminé, Bloqué
- **Par commande** : Recherche par numéro de commande
- **Par date** : Filtrage par période (dans le dashboard)

### 4. Tableau de bord (Dashboard)

#### Routes :
- `GET /projet5/api/dashboard` - Dashboard de base
- `GET /projet5/api/dashboard_avance` - Dashboard avancé avec filtres

#### Indicateurs (KPI) :
- Fiches en cours
- Fiches non débutées
- Fiches terminées
- Fiches bloquées

#### Graphiques :
- Évolution des fiches terminées (7 derniers jours)
- Répartition des temps par poste
- Répartition par poste/service
- Taux de retard/blocage par service
- Fiches en retard

### 5. Détection et correction d'anomalies

#### Route :
- `GET /projet5/api/anomalies` - Détecter les anomalies

#### Types d'anomalies détectées :
1. **Sessions ouvertes sans date de fin** : Sessions ouvertes depuis plus de 24h (hors journée en cours)
2. **Durées incohérentes** : Date de fin antérieure à la date de début
3. **Quantités nulles ou négatives** : NbOp <= 0
4. **Fiches sans opérateur ou opération** : Champs manquants

#### Routes de correction :
- `POST /projet5/api/cloturer_session` - Clôturer une session ouverte
- `POST /projet5/api/corriger_duree_incoherente` - Corriger une durée incohérente
- `POST /projet5/api/corriger_quantite_1` - Mettre quantité à 1
- `POST /projet5/api/corriger_quantite` - Corriger quantité personnalisée
- `POST /projet5/api/corriger_duree` - Corriger date/heure début/fin
- `POST /projet5/api/corriger_operateur_defaut` - Assigner opérateur par défaut (CHAABANE FRIDA)

### 6. Machines en production

#### Routes :
- `GET /projet5/machines_en_production` - Page HTML
- `GET /projet5/api/machines_en_production` - API JSON

Affiche les machines actuellement en production avec :
- Nom de la machine (poste)
- Service
- Client
- Commande
- Fiche
- Date/Heure début
- Opérateur

### 7. Gestion des postes

#### Routes :
- `POST /projet5/api/change_poste` - Changer le poste d'une fiche
- `GET /projet5/api/services_et_postes` - Liste services et postes
- `GET /projet5/api/postes` - Liste des postes
- `GET /projet5/api/postes_du_service_fiche/<id_fiche>` - Postes du service d'une fiche
- `POST /projet5/api/dupliquer_fiche` - Dupliquer une fiche vers un autre poste

### 8. Gestion des opérateurs

#### Routes :
- `GET /projet5/api/personnes` - Liste des opérateurs (atelier 1, non archivés)
- `GET /projet5/api/get_personne_by_code/<code>` - Trouver opérateur par code

#### Fonctionnalités :
- Autocomplétion jQuery UI pour la recherche d'opérateurs
- Affichage : Nom Prénom (Code)
- Filtrage par atelier (Atelier = 1)

### 9. Gestion des opérations

#### Routes :
- `GET /projet5/api/operations/<id_poste>` - Opérations disponibles pour un poste

#### Fonctionnalités :
- Sélection automatique si une seule opération disponible
- Création automatique de `GP_FICHES_OPERATIONS` si opération unique
- Validation : vérification que l'opération est autorisée pour le poste

### 10. Gestion des formes de découpe

#### Fonctionnalités :
- Champ "Forme utilisée" (Remarques dans GP_TRAITEMENTS)
- Mise à jour automatique de `FORMES_DECOUPE.TOTAL_TIRAGES` lors de l'enregistrement
- Autocomplétion pour les noms de formes

### 11. Correction de dossiers

#### Routes :
- `GET /projet5/corriger_dossier` - Page de correction
- `POST /projet5/corriger_dossier` - Exécuter correction
- `POST /projet5/api/corriger_dossier` - API de correction
- `GET /projet5/corriger` - Page de correction automatique des fiches ouvertes
- `POST /projet5/corriger` - Fermer automatiquement les fiches ouvertes

#### Fonctionnalités :
- Correction automatique des heures (virgule → point)
- Recalcul des temps réels
- Mise à jour des dates NULL
- Log détaillé dans `correction_dossier.log`

### 12. Recherche de valeurs NULL

#### Route :
- `GET /projet5/nulls_dossier` - Rechercher les valeurs NULL dans un dossier

#### Fonctionnalités :
- Recherche dans toutes les tables liées à un dossier
- Colonnes de lien détectées automatiquement :
  - `ID_COMMANDE`
  - `ID_FICHE_TRAVAIL`
  - `ID_FICHTRA`
  - `ID`
  - `NumDossier`
  - `Numero`

### 13. Suppression de dossiers

#### Route :
- `GET /projet5/supprimer_dossier` - Page de suppression
- `POST /projet5/supprimer_dossier` - Exécuter suppression

#### Ordre de suppression (tables enfants → parent) :
1. `GS_TAMPONS_LIGNES`
2. `GP_FACT_ACHATS_SSTR`
3. `GP_RESSOURCES_TRAV`
4. `GS_MVT_STOCKS`
5. `GP_RESSOURCES`
6. `GP_FICHES_TRAVAIL`

## Interface utilisateur

### Onglets principaux :

1. **Production** : Tableau principal de suivi des fiches
2. **Tableau de bord** : Dashboard avec KPI et graphiques
3. **Anomalies** : Détection et correction d'anomalies
4. **Machines en production** : Vue en temps réel
5. **Correction dossier** : Outils de correction par dossier
6. **Recherche NULL** : Recherche de valeurs NULL
7. **Suppression dossier** : Suppression complète de dossiers

### Fonctionnalités UI :

- **DataTables** : Tableau interactif avec pagination, tri, recherche
- **Chart.js** : Graphiques pour le dashboard
- **jQuery UI Autocomplete** : Autocomplétion opérateurs et formes
- **Flatpickr** : Sélecteurs de date
- **Bootstrap Modals** : Modales pour diverses actions
- **Toast notifications** : Notifications temporaires
- **Loading overlay** : Indicateur de chargement

## Calculs et logique métier

### Calcul du temps réel

Fonction `recalculer_temps_reel(id_fiche, cursor)` :
- Additionne toutes les durées (HeurFin - HeurDeb) des traitements
- Met à jour `GP_FICHTRA_INT.TpsReel`
- Met à jour `GP_FICHES_TRAVAIL.CtReel`

### Calcul du coût réel

Lors de la fin d'une session :
- Récupère le coût horaire de la machine (`GP_POSTES_TARIF.PrxMach`)
- Calcule : `cout_reel = tps_rel_pass * cout_horaire`
- Met à jour `GP_FICHES_TRAVAIL.CtReel`

### Gestion automatique des états

Lors de la fin d'une fiche :
- `CodIndAv` → `3` (Terminé) pour la fiche courante
- `CodIndAv` → `1` (Prêt) pour la fiche suivante (même commande, même travail, ordre +1)

Lors de l'interruption :
- `CodIndAv` → `2` (En cours) pour la fiche courante
- `CodIndAv` → `1` (Prêt) pour la fiche suivante

### Validation des opérations

Fonction `operation_autorisee(id_poste, id_operation)` :
- Vérifie que l'opération est bien liée au poste dans `GP_POSTES_OP`
- Empêche l'enregistrement d'opérations non autorisées

## Logs et débogage

### Fichiers de log :
- `projet5.log` : Logs des appels API et opérations
- `debug_heure.log` : Logs de débogage des heures
- `correction_dossier.log` : Logs des corrections de dossiers

### Points de log :
- Appels de `fiche_travail()`
- Appels de `fiches_filtrees()`
- Opérations récupérées par poste
- Détails des sauvegardes de traitements
- Erreurs de calcul TpsRelPass/TpsReel/CtReel

## Sécurité et validation

### Validations côté backend :
- Vérification de l'existence des fiches
- Vérification des opérations autorisées
- Validation des quantités (> 0)
- Validation des dates (fin >= début)
- Vérification des sessions ouvertes avant clôture

### Gestion des erreurs :
- Try/except sur toutes les opérations critiques
- Messages d'erreur détaillés
- Retour JSON avec `success: false` en cas d'erreur

## Optimisations

### Cache côté client :
- Cache des données de fiches (5 minutes)
- Cache des services et postes
- Debounce sur les filtres (300ms)

### Optimisations SQL :
- Requêtes avec LEFT JOIN pour éviter les multiples requêtes
- Regroupement par id_fiche pour éviter les doublons
- Filtrage au niveau SQL plutôt que JavaScript

### Performance UI :
- Utilisation de DocumentFragment pour les insertions DOM
- Mise à jour sélective des lignes modifiées
- Chargement asynchrone des données

## Différences avec le workspace local

Le fichier sur prinects (`\\prinects\Apps\logic\projet5.py`) est **beaucoup plus complet** que celui du workspace local (`x:\logic\projet5.py`) :

### Fonctionnalités supplémentaires sur prinects :
1. **Dashboard avancé** avec graphiques et filtres
2. **Détection d'anomalies** avec correction automatique
3. **Machines en production** en temps réel
4. **Correction de dossiers** avec log détaillé
5. **Recherche de valeurs NULL** dans les dossiers
6. **Suppression complète de dossiers**
7. **Duplication de fiches** vers d'autres postes
8. **Historique des sessions** par fiche
9. **Gestion des formes de découpe** avec TOTAL_TIRAGES
10. **Calcul automatique des coûts réels**
11. **Gestion automatique des états** (CodIndAv)
12. **Validation des opérations** autorisées
13. **Logs détaillés** pour le débogage
14. **Gestion des interruptions** et reprises de sessions

### Routes supplémentaires sur prinects :
- `/api/dashboard`
- `/api/dashboard_avance`
- `/api/anomalies`
- `/api/cloturer_session`
- `/api/corriger_*` (plusieurs routes)
- `/api/historique_sessions/<id_fiche>`
- `/api/dupliquer_fiche`
- `/api/postes_du_service_fiche/<id_fiche>`
- `/api/machines_en_production`
- `/corriger`
- `/corriger_dossier`
- `/nulls_dossier`
- `/supprimer_dossier`

## Recommandations

1. **Synchronisation** : Le workspace local devrait être synchronisé avec la version sur prinects pour bénéficier de toutes les fonctionnalités.

2. **Documentation** : Ajouter une documentation API pour toutes les routes.

3. **Tests** : Implémenter des tests unitaires pour les fonctions critiques (calculs, validations).

4. **Performance** : Considérer l'ajout d'index sur les colonnes fréquemment filtrées.

5. **Sécurité** : Ajouter une authentification/autorisation si nécessaire.

6. **Monitoring** : Mettre en place un monitoring des performances et des erreurs.
