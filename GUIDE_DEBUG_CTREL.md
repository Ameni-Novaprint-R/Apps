# Guide de Débogage Étape par Étape - CtRel

## Problème
Le coût réel s'affiche correctement dans le popup (ex: 511,...) mais après l'enregistrement :
- Il s'affiche "-" dans le tableau
- Il est NULL dans la base de données

## Étapes de Vérification

### ÉTAPE 1 : Vérifier le calcul dans le popup (Navigateur)

1. Ouvrir le navigateur et appuyer sur **F12** pour ouvrir la console
2. Aller sur la page Projet 19
3. Cliquer sur "➕ Nouveau dossier"
4. Sélectionner un numéro de dossier (ex: `2025050176`)
5. Cocher des services pour calculer le coût total
6. **Dans la console du navigateur**, chercher les logs :
   ```
   [calculerCtRelPopup] Valeurs pour calcul: {coutTotal: ..., quantite: ..., qteComm: ...}
   [calculerCtRelPopup] Calcul: X / Y * Z = 511.xxx
   ```
7. Vérifier que le champ "Coût Total Réel" affiche `511,xxx` (avec virgule)

**✅ Si OK** → Passer à l'étape 2  
**❌ Si KO** → Le problème est dans `calculerCtRelPopup()`

---

### ÉTAPE 2 : Vérifier l'envoi lors de la sauvegarde (Navigateur)

1. Toujours dans la console du navigateur
2. Cliquer sur "Enregistrer"
3. **Dans la console**, chercher les logs :
   ```
   [saveNewDossierFromPopup] ctRelText depuis DOM: 511,xxx
   [saveNewDossierFromPopup] ctRelText parsé: 511.xxx
   [saveNewDossierFromPopup] Valeurs à sauvegarder: {..., ctRel: 511.xxx, ...}
   [saveNewDossierFromPopup] Payload JSON à envoyer: {..., "ct_rel": 511.xxx, ...}
   ```

**✅ Si `ctRel` est `511.xxx` (nombre)** → Passer à l'étape 3  
**❌ Si `ctRel` est `null` ou `0`** → Le problème est dans la récupération depuis le DOM

---

### ÉTAPE 3 : Vérifier la réception par l'API Flask (Console Flask)

1. Ouvrir la console où tourne Flask (Watchdog)
2. Après avoir cliqué sur "Enregistrer" dans le navigateur
3. **Dans la console Flask**, chercher les logs :
   ```
   [DEBUG api_create_dossier] ct_rel reçu: 511.xxx (type: <class 'float'>)
   [DEBUG api_create_dossier] ct_rel converti: 511.xxx
   [DEBUG api_create_dossier] Création dossier avec ct_rel=511.xxx
   ```

**✅ Si `ct_rel` est `511.xxx`** → Passer à l'étape 4  
**❌ Si `ct_rel` est `None` ou `0`** → Le problème est dans la transmission JSON

---

### ÉTAPE 4 : Vérifier l'enregistrement dans la base de données (Console Flask)

1. Toujours dans la console Flask
2. **Chercher les logs** :
   ```
   [DEBUG create_web_s_dos_encours] [OK] Ajout de CtRel=511.xxx (original=511.xxx, type=<class 'float'>) a l'INSERT
   [DEBUG create_web_s_dos_encours] Colonnes: [..., 'CtRel']
   [DEBUG create_web_s_dos_encours] Valeurs: [..., 511.xxx]
   [DEBUG create_web_s_dos_encours] [OK] Verification apres INSERT: CtRel enregistre = 511.xxx
   ```

**✅ Si `CtRel enregistré = 511.xxx`** → Passer à l'étape 5  
**❌ Si `CtRel enregistré = NULL`** → Le problème est dans l'INSERT SQL

---

### ÉTAPE 5 : Vérifier la récupération depuis la base de données (Console Flask)

1. Après l'enregistrement, le tableau se recharge automatiquement
2. **Dans la console Flask**, chercher les logs :
   ```
   [DEBUG get_web_s_dos_encours] Dossier 2025050176: ct_rel récupéré = 511.xxx
   ```
   OU
   ```
   [DEBUG get_web_s_dos_encours] Dossier 2025050176: ct_rel est NULL dans la base
   ```

**✅ Si `ct_rel récupéré = 511.xxx`** → Passer à l'étape 6  
**❌ Si `ct_rel est NULL`** → La valeur n'a pas été enregistrée dans la base

---

### ÉTAPE 6 : Vérifier l'affichage dans le tableau (Navigateur)

1. Dans la console du navigateur
2. **Chercher les logs** :
   ```
   [createDossierRow] Dossier 2025050176: ct_rel récupéré depuis API = 511.xxx, affiché = 511,xxx
   ```
   OU
   ```
   [createDossierRow] Dossier 2025050176: ct_rel est null ou undefined dans les données
   ```

**✅ Si `ct_rel récupéré = 511.xxx`** → Le problème est résolu !  
**❌ Si `ct_rel est null`** → La valeur n'est pas retournée par l'API

---

## Vérification Directe dans la Base de Données

Si toutes les étapes précédentes sont OK mais que le problème persiste, vérifier directement dans SQL Server :

```sql
-- Vérifier que la colonne existe
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
AND COLUMN_NAME = 'CtRel';

-- Vérifier la valeur pour un dossier spécifique
SELECT ID, Numero_COMMANDES, CoutTotal, CtRel, QteComm_COMMANDES
FROM WEB_S_DOS_ENCOURS
WHERE Numero_COMMANDES = '2025050176'
ORDER BY ID DESC;  -- Le plus récent en premier
```

---

## Script de Test Automatique

Pour tester le flux complet automatiquement :

```bash
cd C:\Apps
.\venv\Scripts\Activate.ps1
python test_ctrel_flow.py 2025050176
```

Ce script teste :
1. La création avec `ct_rel`
2. L'enregistrement dans la base
3. La récupération depuis la base

---

## Points à Vérifier

1. **La colonne CtRel existe-t-elle ?**
   - Si non : exécuter `python add_ctrel_projet19.py`

2. **La valeur est-elle calculée correctement ?**
   - Formule : `(CoutTotal / QteComm_COMMANDES) * Quantité`
   - Vérifier que `QteComm_COMMANDES` n'est pas 0

3. **La valeur est-elle envoyée dans le JSON ?**
   - Vérifier dans la console navigateur le payload

4. **La valeur est-elle reçue par l'API ?**
   - Vérifier dans la console Flask les logs

5. **La valeur est-elle enregistrée dans la base ?**
   - Vérifier directement avec SQL ou les logs Flask

6. **La valeur est-elle récupérée depuis la base ?**
   - Vérifier dans les logs Flask lors du chargement
