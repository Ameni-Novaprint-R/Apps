# Instructions pour nettoyer le cache Python du Projet 19

## 🎯 Objectif
Supprimer les fichiers `__pycache__` du projet 19 pour forcer Python à recharger le code mis à jour.

## 📍 Où exécuter les commandes ?

### ✅ **OUI - Dans un terminal/Invite de commandes séparé**

Les commandes doivent être exécutées **DANS UN TERMINAL/INVITE DE COMMANDES** depuis le répertoire `C:\Apps`, **AVANT** de redémarrer le serveur Flask.

### ❌ **NON - Pas dans app.py**

Les commandes ne doivent **PAS** être ajoutées dans `app.py`. Ce fichier sert uniquement à lancer Flask.

## 🔧 Méthode 1 : Utiliser le script batch (CMD) - Version sélective

### Étape 1 : Ouvrir une Invite de commandes (CMD)
- Appuyez sur `Win + R`
- Tapez `cmd` et appuyez sur `Entrée`
- Naviguez vers le répertoire du projet :
  ```cmd
  cd C:\Apps
  ```

### Étape 2A : Exécuter le script sélectif (avec confirmation)
```cmd
nettoyer_cache_projet19.bat
```
Ce script supprime uniquement les fichiers du projet 19 et vous demande confirmation avant de supprimer les dossiers complets.

### Étape 2B : Version complète (sans confirmation - RECOMMANDÉ)
Pour supprimer automatiquement **TOUS** les fichiers `__pycache__` du projet 19 :
```cmd
nettoyer_cache_projet19_complet.bat
```
Cette version supprime complètement `routes\__pycache__` et `__pycache__` à la racine.

## 🔧 Méthode 2 : Utiliser le script PowerShell

### Étape 1 : Ouvrir PowerShell
- Clic droit sur le menu Démarrer → **Windows PowerShell** (ou **Terminal**)
- Naviguez vers le répertoire du projet :
  ```powershell
  cd C:\Apps
  ```

### Étape 2 : Exécuter le script
```powershell
.\nettoyer_cache_projet19.ps1
```

## 🔧 Méthode 3 : Commandes manuelles (CMD)

Si vous préférez exécuter les commandes manuellement, voici les commandes CMD :

```cmd
cd C:\Apps

REM Supprimer __pycache__ dans routes/
if exist "routes\__pycache__" rmdir /s /q "routes\__pycache__"

REM Supprimer __pycache__ à la racine
if exist "__pycache__" rmdir /s /q "__pycache__"

REM Supprimer les fichiers .pyc individuels
del /q "routes\*.pyc" 2>nul
del /q "*.pyc" 2>nul

echo Cache nettoye avec succes!
```

## 🔧 Méthode 4 : Commandes manuelles (PowerShell)

```powershell
cd C:\Apps

# Supprimer __pycache__ dans routes/
Remove-Item -Path "routes\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue

# Supprimer __pycache__ à la racine
Remove-Item -Path "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue

# Supprimer les fichiers .pyc individuels
Remove-Item -Path "routes\*.pyc" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*.pyc" -Force -ErrorAction SilentlyContinue

Write-Host "Cache nettoye avec succes!"
```

## ⚠️ Important : Après le nettoyage

1. **Arrêtez le serveur Flask** s'il est en cours d'exécution :
   - Trouvez le processus Python qui exécute `app.py`
   - Arrêtez-le (Ctrl+C dans le terminal, ou via le Gestionnaire des tâches)

2. **Redémarrez le serveur Flask** :
   ```cmd
   cd C:\Apps
   .\venv\Scripts\Activate.bat
   python app.py
   ```

## 📋 Ordre des opérations recommandé

1. ✅ Exécuter le script de nettoyage (`nettoyer_cache_projet19.bat`)
2. ✅ Arrêter le serveur Flask (Ctrl+C ou Gestionnaire des tâches)
3. ✅ Attendre 2-3 secondes
4. ✅ Redémarrer le serveur Flask (`python app.py`)

## 🔍 Vérification

Après le nettoyage, vous pouvez vérifier que les fichiers ont été supprimés :

```cmd
dir /s /b __pycache__
dir /s /b *.pyc
```

Si ces commandes ne retournent rien (ou uniquement des fichiers dans `venv\`), le nettoyage a réussi.

## ⚠️ Attention

- **Ne supprimez PAS** les fichiers dans `venv\__pycache__` (ce sont les fichiers de l'environnement virtuel)
- **Ne supprimez PAS** les fichiers dans d'autres projets (projet11, projet12, etc.) sauf si nécessaire
