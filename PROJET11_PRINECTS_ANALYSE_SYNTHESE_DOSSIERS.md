# Analyse – Projet 11 Prinects : Synthèse des dossiers en cours (Suivi Production)

## Important : périmètre de l’analyse

**Demande :** analyser le **projet 11 du Prinects** (application hébergée sur `\\prinects\Apps`), pas notre application hébergée sur 192.168.10.225.

**Situation actuelle :**  
Dans le workspace ouvert (`x:\`) se trouve **notre** application (routes, logic, templates pour projet11, projet13, etc.). Le **code source du Projet 11 Prinects** se trouve sur le serveur **`\\prinects\Apps`** (par exemple `\\prinects\Apps\logic\projet11.py`, `\\prinects\Apps\templates\projet11*.html`), qui **n’est pas présent dans ce workspace**.  
Sans accès à ces fichiers Prinects, une analyse directe du **projet 11 Prinects** (origine des infos, identification des postes Non commencé / En attente / En cours / Terminé) ne peut pas être faite à partir de ce dépôt.

**Pour obtenir une analyse du projet 11 Prinects :**
1. **Ouvrir le dossier Prinects en workspace** dans Cursor (ex. `\\prinects\Apps` ou un lecteur mappé vers ce chemin), puis redemander l’analyse ; ou  
2. **Copier** les fichiers du projet 11 Prinects (logic, templates, routes concernés) dans ce workspace, puis redemander l’analyse.

---

## Ce que l’on peut déduire (notre app et doc existante)

Dans **notre** application (192.168.10.225), le module « Synthèse des dossiers en cours – Suivi Production » est le **Projet 13**, pas le Projet 11. Le **Projet 5 Prinects** (décrit dans `analyse_projet5_prinects.md`) utilise les tables **GP_*** et **CodIndAv** pour les états. Si le **projet 11 Prinects** correspond à la même « Synthèse des dossiers en cours », il est probable qu’il s’appuie sur les mêmes sources (GP_FICHES_TRAVAIL, CodIndAv, etc.) — à confirmer en analysant le code Prinects quand il sera accessible.

---

## 1. Origine des informations

Les données affichées dans la synthèse / planning viennent des tables suivantes :

| Table | Rôle |
|-------|------|
| **GP_FICHES_TRAVAIL** | Fiches de travail (dossiers) ; contient **CodIndAv** = statut d’avancement. |
| **COMMANDES** | Numéro de commande, référence, lien client. |
| **SOCIETES** | Client (RaiSocTri). |
| **GP_POSTES** | Poste (machine/atelier). |
| **GP_SERVICES** | Service (rattachement du poste). |
| **GP_TRAITEMENTS** | Dates/heures début et fin (DteDeb, HeurDeb, DteFin, HeurFin), opérateur (ID_PERSONNE), opération, NbOp. |
| **GP_FICHTRA_INT** ou **GP_FICHES_OPERATIONS** | Temps prévu (TpsPrevDev), temps réel. |
| **PERSONNES** | Nom / prénom de l’opérateur. |
| **GP_POSTES_OP** | Opérations possibles par poste. |

Les fiches sont regroupées par **service** puis par **poste**. Chaque ligne de la synthèse = une fiche de travail (GP_FICHES_TRAVAIL) avec ses traitements et opérations.

---

## 2. Identification des statuts : Non commencé, En attente, En cours, Terminé

Le statut d’une fiche (et donc du “poste” / dossier dans la synthèse) est porté par la colonne **CodIndAv** de la table **GP_FICHES_TRAVAIL**.

| Valeur CodIndAv | Signification (affichage / logique) | Équivalent demandé |
|----------------|-------------------------------------|---------------------|
| **0** | Bloqué (opération précédente non terminée) | Peut correspondre à « En attente » (bloqué) ou à exclure du “Non commencé”. |
| **1** | Prêt à commencer | **Non commencé** / **En attente** |
| **2** | En cours ou interrompue | **En cours** |
| **3** | Terminé | **Terminé** |
| **4** | Terminé et facturé | **Terminé** (sous-type) |

En résumé :

- **Non commencé** : CodIndAv = **1** (prêt à commencer, pas encore démarré).
- **En attente** : CodIndAv = **0** (bloqué) ou **1** (en attente de démarrage), selon la convention Prinects.
- **En cours** : CodIndAv = **2**.
- **Terminé** : CodIndAv = **3** ou **4**.

Dans le code actuel (projet13) :

- Compteurs :  
  - **Non débuté** : CodIndAv IN (0, 1)  
  - **En cours** : CodIndAv = 2  
  - **Terminé** : CodIndAv = 3  
  - **Bloquées** : CodIndAv = 0  
- Libellés dans l’interface :  
  - 0 → « Bloqué (opération précédente non terminée) »  
  - 1 → « Prêt à commencer »  
  - 2 → « En cours ou interrompue »  
  - 3 → « Terminé »  
  - 4 → « Terminé et facturé »

---

## 3. Table et colonne clés pour les statuts

- **Table** : **GP_FICHES_TRAVAIL**
- **Colonne** : **CodIndAv** (entier)
- **Valeurs** : 0 = Bloqué, 1 = Prêt à commencer (Non commencé / En attente), 2 = En cours, 3 = Terminé, 4 = Terminé et facturé.

Les postes (lignes) de la synthèse sont donc identifiés comme **Non commencé**, **En attente**, **En cours** ou **Terminé** via **GP_FICHES_TRAVAIL.CodIndAv**.

---

## 4. Différence Projet 11 / Projet 13 (Suivi Production)

- **Projet 11** (notre app) : gestion des **traitements** dans **WEB_TRAITEMENTS** (DteDeb, DteFin, etc.) avec statuts **En cours** / **Terminé** déduits de la présence de **DteFin** (pas de CodIndAv).
- **Projet 13 (Suivi Production)** : équivalent de la “Synthèse des dossiers en cours” Prinects ; données issues de **GP_FICHES_TRAVAIL**, **GP_TRAITEMENTS**, **COMMANDES**, etc., et statuts portés par **GP_FICHES_TRAVAIL.CodIndAv** (0, 1, 2, 3, 4) comme ci‑dessus.

Ce qui suit décrit l’origine des informations et l’identification des statuts **dans notre Projet 13** (équivalent fonctionnel). Pour le **projet 11 Prinects** proprement dit, il faut analyser le code sur `\\prinects\Apps` (voir ci‑dessus).

---

## Résumé

| Question | Réponse |
|----------|---------|
| **Analyser quel projet ?** | **Projet 11 du Prinects** (sur `\\prinects\Apps`), pas notre app sur 192.168.10.225. |
| **Code Prinects dans ce workspace ?** | **Non.** Le workspace `x:\` contient notre application ; le projet 11 Prinects est sur `\\prinects\Apps`. |
| **Prochaine étape** | Ouvrir `\\prinects\Apps` (ou une copie du projet 11 Prinects) dans Cursor, ou copier les fichiers ici, puis redemander l’analyse. |
