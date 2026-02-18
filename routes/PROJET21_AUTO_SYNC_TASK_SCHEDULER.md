# Configuration Synchronisation Automatique avec Task Scheduler Windows

## Alternative à APScheduler

Si vous ne souhaitez pas installer APScheduler, vous pouvez utiliser le **Planificateur de tâches Windows** pour exécuter la synchronisation automatique chaque jour à 05:00 AM.

## Étapes de configuration

### 1. Créer la tâche planifiée

1. Ouvrir le **Planificateur de tâches** (Task Scheduler)
   - Rechercher "Planificateur de tâches" dans le menu Démarrer
   - Ou exécuter `taskschd.msc`

2. Créer une tâche de base
   - Cliquer sur "Créer une tâche..." (pas "Créer une tâche de base")

3. Onglet **Général**
   - **Nom** : `Projet21 - Synchronisation Automatique`
   - **Description** : `Synchronisation automatique quotidienne de la base de données à 05:00 AM`
   - **Exécuter que l'utilisateur soit connecté ou non** : ✅ Cocher
   - **Exécuter avec les privilèges les plus élevés** : ✅ Cocher (si nécessaire pour accès DB)

4. Onglet **Déclencheurs**
   - Cliquer sur "Nouveau..."
   - **Démarrer la tâche** : `Selon une planification`
   - **Paramètres** : `Quotidiennement`
   - **Heure de début** : `05:00:00`
   - **Répéter la tâche toutes les** : `1 jours`
   - ✅ Cocher "Activer"
   - Cliquer sur "OK"

5. Onglet **Actions**
   - Cliquer sur "Nouveau..."
   - **Action** : `Démarrer un programme`
   - **Programme/script** : Chemin complet vers Python
     ```
     C:\Python\python.exe
     ```
     (Adapter selon votre installation Python)
   - **Ajouter des arguments** :
     ```
     "X:\routes\projet21_auto_sync_task.py"
     ```
     (Adapter le chemin selon votre installation)
   - **Démarrer dans** :
     ```
     X:\
     ```
     (Le répertoire racine de votre projet)
   - Cliquer sur "OK"

6. Onglet **Conditions**
   - ✅ Décocher "Mettre en veille l'ordinateur pour exécuter cette tâche"
   - ✅ Cocher "Réveiller l'ordinateur pour exécuter cette tâche" (optionnel)
   - ✅ Cocher "Démarrer la tâche uniquement si l'ordinateur est branché sur secteur" (optionnel)

7. Onglet **Paramètres**
   - ✅ Cocher "Autoriser l'exécution de la tâche à la demande"
   - ✅ Cocher "Exécuter la tâche dès que possible après un démarrage manqué"
   - ✅ Cocher "Si la tâche échoue, redémarrer toutes les" : `10 minutes`
   - **Nombre de nouvelles tentatives** : `3`
   - ✅ Cocher "Arrêter la tâche si elle s'exécute plus longtemps que" : `2 heures`

8. Cliquer sur "OK"
   - Entrer le mot de passe de l'utilisateur si demandé

### 2. Tester la tâche

1. Dans le Planificateur de tâches, sélectionner la tâche créée
2. Clic droit → **Exécuter**
3. Vérifier les résultats dans :
   - `sync_results/last_auto_sync_result.json` (si problèmes détectés)
   - Email reçu (si erreur ou problème)

### 3. Vérifier les logs

Les logs sont affichés dans :
- La sortie standard du script (visible dans l'historique de la tâche)
- Les emails envoyés en cas d'erreur

Pour voir l'historique d'exécution :
1. Sélectionner la tâche dans le Planificateur
2. Onglet **Historique** en bas de la fenêtre

## Avantages de cette méthode

✅ Pas besoin d'installer APScheduler  
✅ Fonctionne même si Flask n'est pas démarré (script standalone)  
✅ Gestion native par Windows  
✅ Peut être exécuté manuellement depuis le Planificateur  
✅ Logs intégrés dans le Planificateur de tâches  

## Inconvénients

❌ Nécessite que le serveur Windows soit allumé à 05:00 AM  
❌ Configuration manuelle dans Windows (pas depuis l'interface web)  
❌ Pas de synchronisation avec l'état dans l'interface web  

## Alternative : Script PowerShell

Si vous préférez utiliser PowerShell, vous pouvez créer un script `.ps1` :

```powershell
# sync_projet21.ps1
$python = "C:\Python\python.exe"
$script = "X:\routes\projet21_auto_sync_task.py"
& $python $script
```

Puis dans le Planificateur de tâches :
- **Programme/script** : `powershell.exe`
- **Ajouter des arguments** : `-ExecutionPolicy Bypass -File "X:\routes\sync_projet21.ps1"`

## Désactiver la synchronisation

Pour désactiver temporairement :
1. Ouvrir le Planificateur de tâches
2. Trouver la tâche "Projet21 - Synchronisation Automatique"
3. Clic droit → **Désactiver**

Pour réactiver :
1. Clic droit → **Activer**

## Note importante

Si vous utilisez cette méthode avec Task Scheduler, vous pouvez **supprimer le code APScheduler** de `app.py` pour éviter les erreurs d'import. Le système fonctionnera indépendamment de Flask.
