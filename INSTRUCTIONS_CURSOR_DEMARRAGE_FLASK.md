# Instructions pour que Cursor démarre Flask automatiquement

## Solution Implémentée

J'ai créé plusieurs scripts que je peux utiliser pour démarrer Flask automatiquement quand nécessaire.

## Scripts Disponibles

### 1. `cursor_demarrer_flask.ps1` ⭐ (Recommandé pour Cursor)
Script PowerShell simple et rapide que je peux exécuter directement.

**Utilisation par Cursor:**
```powershell
cd C:\Apps
.\cursor_demarrer_flask.ps1
```

**Fonctionnalités:**
- ✅ Vérifie si Flask est déjà en cours
- ✅ Démarre Flask automatiquement si nécessaire
- ✅ Démarre en arrière-plan (fenêtre minimisée)
- ✅ Attend et vérifie que Flask répond
- ✅ Retourne un code de sortie clair

### 2. `demarrer_flask_silencieux.py`
Script Python sans dépendances externes (utilise urllib au lieu de requests).

**Utilisation:**
```powershell
cd C:\Apps
python demarrer_flask_silencieux.py
```

## Comment Cursor l'utilise

Quand j'ai besoin de tester quelque chose qui nécessite Flask (comme vérifier une route, tester un template, etc.), je peux maintenant :

1. **Vérifier si Flask tourne** avec une simple requête HTTP
2. **Démarrer Flask automatiquement** si nécessaire en exécutant le script
3. **Continuer avec mes tests** une fois Flask démarré

## Exemple d'Utilisation Automatique

Quand je dois tester une route Flask, je peux maintenant faire :

```powershell
# 1. Vérifier/démarrer Flask
cd C:\Apps
.\cursor_demarrer_flask.ps1

# 2. Attendre quelques secondes
Start-Sleep -Seconds 3

# 3. Tester la route
curl.exe http://localhost:5000/projet11/statistiques
```

## Avantages

- ✅ **Automatique** : Je peux démarrer Flask sans intervention manuelle
- ✅ **Intelligent** : Vérifie d'abord si Flask tourne déjà
- ✅ **Silencieux** : Démarre en arrière-plan sans fenêtre visible
- ✅ **Rapide** : Script simple et efficace

## Notes

- Flask démarre dans une fenêtre minimisée pour ne pas gêner
- Le script attend jusqu'à 10 secondes pour que Flask démarre
- Si Flask ne démarre pas, le script retourne un code d'erreur
