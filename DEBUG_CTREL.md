# Guide de Débogage - Problème CtRel (Coût Total Réel)

## Problème
Le coût réel s'affiche correctement dans le popup (ex: 511,...) mais après l'enregistrement :
- Il s'affiche "-" dans le tableau
- Il est NULL dans la base de données

## Étapes de Vérification

### Étape 1 : Vérifier le calcul dans le popup
1. Ouvrir le navigateur (F12 pour ouvrir la console)
2. Ouvrir le popup "Nouveau dossier"
3. Sélectionner un numéro de dossier (ex: 2025050176)
4. Cocher des services pour calculer le coût total
5. **Vérifier dans la console du navigateur** :
   - Chercher les logs `[calculerCtRelPopup]`
   - Vérifier que le calcul est fait : `Calcul: X / Y * Z = 511.xxx`
   - Vérifier que la valeur est affichée dans le champ `popup-ct-rel`

**Si le calcul ne fonctionne pas** → Le problème est dans `calculerCtRelPopup()`

### Étape 2 : Vérifier l'envoi lors de la sauvegarde
1. Toujours dans la console du navigateur
2. Cliquer sur "Enregistrer"
3. **Vérifier dans la console** :
   - Chercher les logs `[saveNewDossierFromPopup]`
   - Vérifier `ctRelText` : doit contenir "511,xxx" (avec virgule)
   - Vérifier `ctRel` : doit contenir `511.xxx` (nombre, pas null)
   - Vérifier `Payload JSON à envoyer` : doit contenir `"ct_rel": 511.xxx`

**Si ctRel est null ou 0** → Le problème est dans la récupération depuis le DOM

### Étape 3 : Vérifier la réception par l'API Flask
1. Ouvrir la console Flask (où tourne le serveur)
2. Après avoir cliqué sur "Enregistrer"
3. **Vérifier dans la console Flask** :
   - Chercher les logs `[DEBUG api_create_dossier]`
   - Vérifier `ct_rel reçu: 511.xxx (type: <class 'float'>)`
   - Vérifier `ct_rel converti: 511.xxx`
   - Vérifier `Création dossier avec ct_rel=511.xxx`

**Si ct_rel est None ou 0** → Le problème est dans la transmission JSON

### Étape 4 : Vérifier l'enregistrement dans la base de données
1. Toujours dans la console Flask
2. **Vérifier les logs** :
   - Chercher `[DEBUG create_web_s_dos_encours]`
   - Vérifier `Ajout de CtRel=511.xxx (original=511.xxx, type=<class 'float'>)`
   - Vérifier `Colonnes: [..., 'CtRel']`
   - Vérifier `Valeurs: [..., 511.xxx]`
   - Vérifier `✅ Vérification après INSERT: CtRel enregistré = 511.xxx`

**Si CtRel n'est pas dans les colonnes** → La colonne n'existe pas dans la base
**Si CtRel est NULL après INSERT** → Le problème est dans l'INSERT SQL

### Étape 5 : Vérifier la récupération depuis la base de données
1. Après l'enregistrement, le tableau se recharge automatiquement
2. **Vérifier dans la console Flask** :
   - Chercher `[DEBUG get_web_s_dos_encours]`
   - Chercher `Dossier 2025050176: ct_rel récupéré = 511.xxx`
   - OU `Dossier 2025050176: ct_rel est NULL dans la base`

**Si ct_rel est NULL** → La valeur n'a pas été enregistrée dans la base

### Étape 6 : Vérifier l'affichage dans le tableau
1. Dans la console du navigateur
2. **Vérifier les logs** :
   - Chercher `[createDossierRow]`
   - Chercher `Dossier 2025050176: ct_rel récupéré depuis API = 511.xxx`
   - OU `Dossier 2025050176: ct_rel est null ou undefined dans les données`

**Si ct_rel est null** → La valeur n'est pas retournée par l'API

## Vérification Directe dans la Base de Données

Pour vérifier directement dans SQL Server :

```sql
-- Vérifier que la colonne existe
SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
AND COLUMN_NAME = 'CtRel';

-- Vérifier la valeur pour un dossier spécifique
SELECT ID, Numero_COMMANDES, CoutTotal, CtRel, QteComm_COMMANDES
FROM WEB_S_DOS_ENCOURS
WHERE Numero_COMMANDES = '2025050176';
```

## Points à Vérifier

1. **La colonne CtRel existe-t-elle ?**
   - Si non : exécuter `add_ctrel_projet19.py`

2. **La valeur est-elle calculée correctement ?**
   - Formule : `(CoutTotal / QteComm_COMMANDES) * Quantité`
   - Vérifier que QteComm_COMMANDES n'est pas 0

3. **La valeur est-elle envoyée dans le JSON ?**
   - Vérifier dans la console navigateur le payload

4. **La valeur est-elle reçue par l'API ?**
   - Vérifier dans la console Flask les logs

5. **La valeur est-elle enregistrée dans la base ?**
   - Vérifier directement avec SQL ou les logs Flask

6. **La valeur est-elle récupérée depuis la base ?**
   - Vérifier dans les logs Flask lors du chargement
