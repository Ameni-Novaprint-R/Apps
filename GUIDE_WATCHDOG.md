# Guide d'utilisation de Flask avec Watchdog

## 📋 Vue d'ensemble

Cette solution utilise **Watchdog** pour surveiller les modifications de fichiers et redémarrer Flask automatiquement. Elle est optimisée pour Windows Server et gère automatiquement le cache Python.

## 🚀 Démarrage rapide

### Option 1 : PowerShell (recommandé)
```powershell
cd C:\Apps
.\run-flask-watchdog.ps1
```

### Option 2 : Batch
```cmd
cd C:\Apps
run-flask-watchdog.bat
```

### Option 3 : Python direct
```cmd
cd C:\Apps
.\venv\Scripts\activate
python run_flask_with_watchdog.py
```

## ✨ Fonctionnalités

### Rechargement automatique
- ✅ Surveille les fichiers `.py`, `.html`, `.js`, `.css`, `.sql`
- ✅ Redémarre Flask automatiquement lors des modifications
- ✅ Nettoie automatiquement le cache Python (`__pycache__`)
- ✅ Délai anti-rebond pour éviter les rechargements trop fréquents

### Exclusions automatiques
Les répertoires suivants sont ignorés :
- `__pycache__`
- `.git`
- `venv` / `.venv`
- `node_modules`
- `.cursor`

## 🔧 Configuration

### Variables d'environnement
- `FLASK_USE_WATCHDOG=true` : Active le mode watchdog dans Flask (désactive le rechargement intégré)

### Personnalisation
Pour modifier les extensions surveillées ou les répertoires exclus, éditez `run_flask_with_watchdog.py` :
```python
WATCHED_EXTENSIONS = {'.py', '.html', '.js', '.css', '.sql'}
EXCLUDED_DIRS = {'__pycache__', '.git', 'venv', '.venv', 'node_modules', '.cursor'}
```

## 📝 Utilisation

1. **Démarrer Flask avec Watchdog**
   ```powershell
   .\run-flask-watchdog.ps1
   ```

2. **Modifier un fichier**
   - Modifiez n'importe quel fichier Python, HTML, JS, CSS ou SQL
   - Watchdog détecte automatiquement la modification
   - Flask redémarre automatiquement

3. **Arrêter Flask**
   - Appuyez sur `Ctrl+C` dans la console
   - Flask et Watchdog s'arrêtent proprement

## 🐛 Dépannage

### Flask ne redémarre pas après une modification
1. Vérifiez que le fichier modifié a une extension surveillée (`.py`, `.html`, etc.)
2. Vérifiez que le fichier n'est pas dans un répertoire exclu
3. Consultez les logs dans la console pour voir les messages de Watchdog

### Erreurs de cache
- Watchdog nettoie automatiquement le cache avant chaque redémarrage
- Si des problèmes persistent, supprimez manuellement les répertoires `__pycache__`

### Watchdog non installé
```cmd
.\venv\Scripts\activate
pip install watchdog
```

## 🔄 Migration depuis l'ancien système

### Ancien système (sans Watchdog)
```cmd
python app.py
```

### Nouveau système (avec Watchdog)
```cmd
python run_flask_with_watchdog.py
```
ou
```powershell
.\run-flask-watchdog.ps1
```

## 📊 Avantages par rapport au rechargement intégré de Flask

| Fonctionnalité | Flask intégré | Watchdog |
|----------------|---------------|----------|
| Fiabilité sur Windows Server | ⚠️ Variable | ✅ Excellente |
| Gestion du cache | ❌ Manuelle | ✅ Automatique |
| Délai anti-rebond | ❌ Non | ✅ Oui |
| Surveillance de plusieurs extensions | ⚠️ Limitée | ✅ Complète |
| Logs détaillés | ⚠️ Basiques | ✅ Détaillés |

## 🎯 Bonnes pratiques

1. **Utilisez Watchdog en développement**
   - Pour la production, utilisez un serveur WSGI (Waitress, Gunicorn)

2. **Surveillez les logs**
   - Les messages de Watchdog indiquent quand Flask redémarre
   - Surveillez les erreurs dans la console

3. **Évitez les modifications trop fréquentes**
   - Watchdog a un délai anti-rebond de 1 seconde
   - Évitez de sauvegarder plusieurs fois rapidement

## 📞 Support

En cas de problème :
1. Vérifiez les logs dans la console
2. Vérifiez que Watchdog est installé : `pip list | findstr watchdog`
3. Vérifiez que les fichiers modifiés sont dans les extensions surveillées
