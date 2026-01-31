# Instructions pour la Synchronisation GitHub

## ⚠️ IMPORTANT : Git doit être accessible

Git est installé mais n'est pas encore accessible dans PowerShell.

## Solution 1 : Redémarrer PowerShell (RECOMMANDÉ)

1. **Fermez complètement PowerShell** (fermez toutes les fenêtres)
2. **Rouvrez PowerShell en tant qu'administrateur**
3. **Exécutez** :
   ```powershell
   cd c:\Apps
   .\sync-github-direct.ps1
   ```

## Solution 2 : Trouver le chemin de Git manuellement

1. Ouvrez l'Explorateur de fichiers
2. Allez dans `C:\Program Files\` ou `C:\Program Files (x86)\`
3. Cherchez le dossier `Git`
4. Notez le chemin complet (ex: `C:\Program Files\Git\bin\git.exe`)

Ensuite, modifiez le script `sync-github-direct.ps1` pour utiliser ce chemin.

## Solution 3 : Ajouter Git au PATH système

1. Ouvrez "Variables d'environnement" (recherchez dans le menu Démarrer)
2. Dans "Variables système", trouvez "Path"
3. Cliquez sur "Modifier"
4. Ajoutez le chemin de Git (ex: `C:\Program Files\Git\bin`)
5. Redémarrez PowerShell

## Après avoir résolu le problème Git

Une fois que `git --version` fonctionne, exécutez :

```powershell
cd c:\Apps
.\sync-github-direct.ps1
```

Le script vous demandera :
- **Nom d'utilisateur GitHub** (ex: Ameni-Novaprint-R)
- **Nom du dépôt GitHub** (ex: Apps)

Puis il effectuera la synchronisation NON DESTRUCTIVE avec GitHub.

---

**Rappel** : La synchronisation est STRICTEMENT NON DESTRUCTIVE.
- Aucun fichier ne sera supprimé
- Aucun --force ne sera utilisé
- Tous les fichiers de la page web seront préservés
