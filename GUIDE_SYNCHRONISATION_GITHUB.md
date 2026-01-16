# Guide de Synchronisation GitHub - NON DESTRUCTIVE

## ⚠️ IMPORTANT : Synchronisation NON DESTRUCTIVE

Cette synchronisation respecte strictement les règles suivantes :
- ✅ **Aucune suppression** de fichiers ou de données
- ✅ **Aucun --force** ou écrasement
- ✅ **Préservation totale** du code existant et du fonctionnement de la page web
- ✅ **Tous les fichiers utiles** pour le fonctionnement de la page web sont préservés

## 📋 Prérequis

1. **Git doit être installé** sur votre système
   - Télécharger depuis : https://git-scm.com/download/win
   - Ou vérifier l'installation : `git --version`

2. **Compte GitHub configuré**
   - Email : ameni.compta@novaprint.tn
   - Le dépôt GitHub doit exister (créer sur https://github.com si nécessaire)

## 🚀 Utilisation du Script de Synchronisation

### Méthode 1 : Script Automatique (Recommandé)

1. **Ouvrir PowerShell en tant qu'administrateur**

2. **Exécuter le script** :
   ```powershell
   cd c:\Apps
   .\sync-github.ps1
   ```

3. **Suivre les instructions** :
   - Le script vous demandera le nom du dépôt GitHub
   - Il vérifiera l'état actuel
   - Il proposera de commiter les changements si nécessaire
   - Il fera un merge non destructif si le dépôt distant existe
   - Il poussera les changements sans --force

### Méthode 2 : Commandes Manuelles

Si vous préférez faire la synchronisation manuellement :

#### 1. Configuration Git
```powershell
cd c:\Apps
git config user.email "ameni.compta@novaprint.tn"
git config user.name "ameni.compta"
```

#### 2. Vérifier l'état
```powershell
git status
```

#### 3. Ajouter les fichiers (si nécessaire)
```powershell
git add .
git commit -m "Synchronisation initiale avec GitHub"
```

#### 4. Ajouter le remote GitHub
```powershell
# Remplacer NOM_DU_REPO par le nom de votre dépôt
git remote add origin https://github.com/ameni.compta@novaprint.tn/NOM_DU_REPO.git
```

#### 5. Récupérer les données distantes (si le dépôt existe déjà)
```powershell
git fetch origin
```

#### 6. Fusionner (sans écrasement)
```powershell
git merge origin/main --no-ff -m "Merge: Synchronisation avec GitHub"
```

#### 7. Pousser vers GitHub (SANS --force)
```powershell
git push -u origin main
```

## 🔒 Sécurité

- Les fichiers sensibles sont protégés par `.gitignore`
- Les mots de passe et configurations locales ne seront **jamais** commités
- Le script ne fait **jamais** de `--force`, préservant ainsi tout l'historique

## 📁 Fichiers Préservés

Tous les fichiers nécessaires au fonctionnement de la page web sont préservés :
- ✅ Tous les fichiers Python (`.py`)
- ✅ Tous les templates HTML (`.html`)
- ✅ Tous les fichiers CSS et JavaScript
- ✅ Tous les fichiers de configuration nécessaires
- ✅ Tous les fichiers statiques
- ✅ L'historique Git complet

## ⚠️ En Cas de Problème

### Si Git n'est pas trouvé :
1. Installer Git depuis https://git-scm.com/download/win
2. Redémarrer PowerShell
3. Réessayer le script

### Si le dépôt distant a des conflits :
1. Le script créera une branche de sauvegarde
2. Résoudre les conflits manuellement
3. Commiter les changements
4. Pousser à nouveau

### Si l'authentification échoue :
1. Vérifier que le dépôt GitHub existe
2. Vérifier les droits d'accès au dépôt
3. Utiliser un Personal Access Token si nécessaire

## 📞 Support

En cas de problème, vérifier :
- Que Git est installé et dans le PATH
- Que le dépôt GitHub existe
- Que vous avez les droits d'accès
- Que les identifiants sont corrects

---

**Rappel** : Cette synchronisation est **STRICTEMENT NON DESTRUCTIVE**. 
Aucun fichier ne sera supprimé ou écrasé.
