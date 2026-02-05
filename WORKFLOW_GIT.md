# Workflow Git pour la Synchronisation GitHub

## Principe : Conservation de Toutes les Versions

**Objectif** : Chaque synchronisation crée une nouvelle version (commit) dans l'historique Git. Toutes les versions restent accessibles et peuvent être restaurées à tout moment.

---

## 📋 Workflow Standard de Synchronisation

### Étape 1 : Vérifier l'état actuel
```powershell
cd x:\
git status
```

### Étape 2 : Ajouter les fichiers modifiés et nouveaux
```powershell
# Ajouter tous les fichiers modifiés et nouveaux
git add -A

# OU ajouter sélectivement :
git add fichier1.py fichier2.html
```

### Étape 3 : Créer un commit avec un message descriptif
```powershell
git commit -m "Description claire des changements - Date"
```

**Exemples de messages de commit :**
- `"Mise à jour projet1: ajout palette violet - 2026-02-05"`
- `"Amélioration authentification et routes - 2026-02-05"`
- `"Ajout scripts migration et vérification - 2026-02-05"`
- `"Correction styles CSS et templates - 2026-02-05"`

### Étape 4 : Pousser vers GitHub
```powershell
git push origin main
```

**Important** : Ne jamais utiliser `--force` sauf en cas de nécessité absolue et avec précaution.

---

## 🔍 Consulter l'Historique des Versions

### Voir tous les commits
```powershell
git log --oneline
```

### Voir les détails d'un commit spécifique
```powershell
git show <hash_du_commit>
# Exemple : git show 82d4c4c
```

### Voir les changements entre deux versions
```powershell
git diff <commit1> <commit2>
# Exemple : git diff 82d4c4c HEAD
```

### Voir l'historique d'un fichier spécifique
```powershell
git log --oneline -- <chemin/vers/fichier>
# Exemple : git log --oneline -- templates/projet1.html
```

---

## 🔄 Restaurer une Version Intermédiaire

### Option 1 : Consulter une version sans modifier le dépôt
```powershell
git checkout <hash_du_commit> -- <chemin/vers/fichier>
# Exemple : git checkout 82d4c4c -- templates/projet1.html
```

### Option 2 : Créer une branche à partir d'une version passée
```powershell
git checkout -b branche-restauration <hash_du_commit>
# Exemple : git checkout -b restauration-projet1 82d4c4c
```

### Option 3 : Restaurer un fichier à une version précédente
```powershell
# Voir les versions disponibles
git log --oneline -- templates/projet1.html

# Restaurer le fichier à une version spécifique
git checkout <hash_du_commit> -- templates/projet1.html

# Créer un commit pour cette restauration
git commit -m "Restauration templates/projet1.html à la version <hash> - 2026-02-05"
```

---

## 📊 Comparer les Versions

### Comparer la version actuelle avec la dernière version sur GitHub
```powershell
git diff origin/main
```

### Comparer deux commits spécifiques
```powershell
git diff <commit1> <commit2>
```

### Comparer un fichier entre deux versions
```powershell
git diff <commit1> <commit2> -- <chemin/vers/fichier>
```

### Voir les fichiers modifiés entre deux commits
```powershell
git diff --name-only <commit1> <commit2>
```

---

## 🏷️ Bonnes Pratiques

### Messages de commit clairs
- Utiliser des messages descriptifs
- Inclure la date dans le message
- Grouper les changements liés dans le même commit
- Un commit = une fonctionnalité ou correction logique

### Fréquence de synchronisation
- Synchroniser régulièrement (quotidiennement ou après chaque fonctionnalité majeure)
- Ne pas attendre trop longtemps entre les commits
- Chaque version importante doit avoir son propre commit

### Organisation des commits
- Un commit pour les modifications de templates
- Un commit pour les modifications de logique métier
- Un commit pour les scripts et migrations
- Un commit pour les styles CSS

---

## ⚠️ Règles Importantes

1. **JAMAIS de `--force`** sur la branche principale sans raison valable
2. **Toujours vérifier** avec `git status` avant de committer
3. **Toujours créer un commit** avant de pousser (ne jamais pousser directement)
4. **Conserver l'historique** : ne pas réécrire l'historique de la branche principale
5. **Messages descriptifs** : faciliter la recherche dans l'historique

---

## 🔐 Authentification GitHub

Pour pousser vers GitHub, vous aurez besoin d'un **Personal Access Token** :

1. Allez sur : https://github.com/settings/tokens
2. Créez un nouveau token avec la permission **"repo"**
3. Utilisez ce token comme mot de passe lors du `git push`

---

## 📝 Exemple Complet de Synchronisation

```powershell
# 1. Vérifier l'état
cd x:\
git status

# 2. Ajouter les changements
git add -A

# 3. Créer un commit
git commit -m "Mise à jour projets et ajout scripts migration - 2026-02-05"

# 4. Pousser vers GitHub
git push origin main

# 5. Vérifier que tout est synchronisé
git status
```

---

## 🆘 En Cas de Problème

### Annuler les changements non commités
```powershell
git restore <fichier>
# OU pour tous les fichiers
git restore .
```

### Modifier le dernier commit (avant push)
```powershell
git commit --amend -m "Nouveau message"
```

### Voir les différences avant de committer
```powershell
git diff
```

---

**Rappel** : Ce workflow garantit que toutes les versions sont conservées dans l'historique Git et accessibles à tout moment.
