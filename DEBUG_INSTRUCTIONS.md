# Instructions de débogage - Problème des coûts à 0.000

## ÉTAPE 1 : Vérifier que Flask a bien rechargé le code

1. **Arrêtez Flask** (Ctrl+C dans la fenêtre Watchdog ou PowerShell où Flask tourne)

2. **Redémarrez Flask** avec Watchdog :
   ```powershell
   cd C:\Apps
   .\run-flask-watchdog.bat
   ```

3. **Attendez** que Flask démarre complètement (vous devriez voir "Flask démarré")

## ÉTAPE 2 : Vérifier les logs Flask lors du chargement d'un dossier

1. **Ouvrez le popup** dans l'application web avec un numéro de dossier (ex: 2025050176)

2. **Regardez la console Flask** où Watchdog tourne

3. **Vous DEVRIEZ voir** des logs comme :
   ```
   [API DEBUG] Détails complets des X services:
   [API DEBUG] #1 - nom='CONDITIONNEMENT', cout=2.04, id=CONDITIONNEMENT_415697, id_fiche=415697
   [API DEBUG] #2 - nom='Massicotage', cout=10.75, id=Massicotage_415693, id_fiche=415693
   ...
   ```

4. **Si vous NE VOYEZ PAS ces logs**, le code n'a pas été rechargé. Dans ce cas :
   - Arrêtez Flask complètement
   - Supprimez le dossier `__pycache__` :
     ```powershell
     Remove-Item -Recurse -Force C:\Apps\__pycache__
     Remove-Item -Recurse -Force C:\Apps\routes\__pycache__
     ```
   - Redémarrez Flask

## ÉTAPE 3 : Vérifier la réponse HTTP directement

1. **Ouvrez PowerShell** (nouvelle fenêtre)

2. **Exécutez cette commande** (remplacez 2025050176 par un numéro de dossier valide) :
   ```powershell
   $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/projet19/api/postes/2025050176"
   $json = $response.Content | ConvertFrom-Json
   $json.postes[0] | ConvertTo-Json -Depth 10
   ```

3. **Vous DEVRIEZ voir** quelque chose comme :
   ```json
   {
     "cout": 2.04,
     "id": "CONDITIONNEMENT_415697",
     "id_fiche_travail": 415697,
     "nom": "CONDITIONNEMENT",
     "nom_poste": "CONDITIONNEMENT"
   }
   ```

4. **Si vous NE VOYEZ PAS le champ "cout"**, il y a un problème avec Flask qui ne retourne pas les données.

## ÉTAPE 4 : Vérifier la console du navigateur

1. **Ouvrez l'application** dans votre navigateur (Chrome/Firefox/Edge)

2. **Ouvrez la console développeur** :
   - **Chrome/Edge** : Appuyez sur `F12` ou `Ctrl+Shift+I`
   - **Firefox** : Appuyez sur `F12` ou `Ctrl+Shift+K`

3. **Allez dans l'onglet "Console"**

4. **Ouvrez le popup** et sélectionnez un numéro de dossier

5. **Vous DEVRIEZ voir** des logs comme :
   ```
   [loadServicesInPopup] Données complètes reçues: {...}
   [loadServicesInPopup] Premier service complet: {...}
   [loadServiceCosts] Services reçus: [...]
   [loadServiceCosts] Service: CONDITIONNEMENT, ID: ..., Cout brut: 2.04, Cout parsé: 2.04
   ```

6. **Copiez-collez** tous les logs de la console ici pour que je puisse voir ce qui se passe

## ÉTAPE 5 : Vérifier le cache du navigateur

1. **Videz le cache** :
   - **Chrome/Edge** : `Ctrl+Shift+Delete` → Cochez "Images et fichiers en cache" → Effacer
   - **Firefox** : `Ctrl+Shift+Delete` → Cochez "Cache" → Effacer

2. **Rechargez la page** avec `Ctrl+F5` (rechargement forcé)

3. **Réessayez** d'ouvrir le popup

## ÉTAPE 6 : Vérifier directement dans le code source

1. **Ouvrez** `C:\Apps\templates\projet19.html`

2. **Cherchez** la ligne qui contient `loadServiceCosts` (vers la ligne 1856)

3. **Vérifiez** que le code contient bien :
   ```javascript
   let cout = service.cout !== undefined && service.cout !== null ? parseFloat(service.cout) : 0.0;
   ```

4. **Vérifiez** aussi que `service.cout` est bien utilisé et pas `service.coutCtPrevDev` ou autre

## Ce que vous devez me dire :

1. **Les logs Flask** : Voyez-vous les logs `[API DEBUG]` avec les valeurs `cout` ?
2. **La réponse HTTP** : La commande PowerShell retourne-t-elle bien le champ `cout` ?
3. **La console navigateur** : Voyez-vous les logs JavaScript et quelles valeurs sont affichées ?
4. **Le résultat final** : Les services s'affichent-ils toujours avec 0.000 ?
