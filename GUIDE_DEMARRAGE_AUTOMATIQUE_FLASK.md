# Guide de Démarrage Automatique de Flask

Ce guide présente plusieurs solutions pour démarrer Flask automatiquement.

## 🚀 Solutions Disponibles

### 1. Script PowerShell (Recommandé) ⭐

**Fichier:** `demarrer_flask_auto.ps1`

**Utilisation:**
```powershell
cd C:\Apps
.\demarrer_flask_auto.ps1
```

**Fonctionnalités:**
- ✅ Vérifie si Flask est déjà en cours d'exécution
- ✅ Détecte et active automatiquement l'environnement virtuel
- ✅ Démarre Flask dans une nouvelle fenêtre PowerShell
- ✅ Vérifie que Flask répond correctement
- ✅ Affiche le statut de démarrage

**Avantages:**
- Interface claire avec messages colorés
- Gestion intelligente des processus existants
- Vérification automatique du démarrage

---

### 2. Script Python

**Fichier:** `demarrer_flask_auto.py`

**Utilisation:**
```powershell
cd C:\Apps
python demarrer_flask_auto.py
```

**Fonctionnalités:**
- ✅ Compatible Windows/Linux/Mac
- ✅ Détection automatique de Flask en cours
- ✅ Démarrage dans un processus séparé
- ✅ Vérification périodique du statut

**Avantages:**
- Portable (fonctionne sur plusieurs OS)
- Peut être intégré dans d'autres scripts Python

---

### 3. Script Batch (Windows)

**Fichier:** `demarrer_flask_auto.bat`

**Utilisation:**
```cmd
cd C:\Apps
demarrer_flask_auto.bat
```

**Fonctionnalités:**
- ✅ Simple double-clic pour démarrer
- ✅ Compatible avec toutes les versions de Windows
- ✅ Pas besoin de PowerShell

**Avantages:**
- Très simple à utiliser
- Idéal pour les utilisateurs non techniques

---

### 4. Tâche Planifiée Windows (Démarrage Automatique)

**Fichier:** `creer_tache_planifiee_flask.ps1`

**Utilisation:**
```powershell
# Exécuter en tant qu'administrateur
cd C:\Apps
.\creer_tache_planifiee_flask.ps1
```

**Options de déclenchement:**
1. **Au démarrage de Windows** - Flask démarre automatiquement au boot
2. **À l'ouverture de session** - Flask démarre quand vous vous connectez
3. **À une heure spécifique** - Flask démarre tous les jours à l'heure choisie

**Avantages:**
- ✅ Démarrage complètement automatique
- ✅ Pas besoin d'intervention manuelle
- ✅ Fonctionne même après redémarrage du serveur

**Gestion de la tâche:**
```powershell
# Voir la tâche
Get-ScheduledTask -TaskName "DemarrerFlaskAuto"

# Exécuter la tâche manuellement
Start-ScheduledTask -TaskName "DemarrerFlaskAuto"

# Supprimer la tâche
Unregister-ScheduledTask -TaskName "DemarrerFlaskAuto" -Confirm:$false
```

---

## 📋 Comparaison des Solutions

| Solution | Facilité | Automatisation | Recommandation |
|----------|----------|-----------------|----------------|
| PowerShell | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | **Pour usage quotidien** |
| Python | ⭐⭐⭐⭐ | ⭐⭐⭐ | Pour intégration dans scripts |
| Batch | ⭐⭐⭐⭐⭐ | ⭐⭐ | Pour utilisateurs non techniques |
| Tâche planifiée | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **Pour serveur de production** |

---

## 🔧 Utilisation Recommandée

### Pour le Développement
Utilisez le script PowerShell (`demarrer_flask_auto.ps1`) :
- Démarrage rapide et contrôlé
- Messages clairs sur le statut
- Facile à arrêter (fermer la fenêtre)

### Pour la Production
Créez une tâche planifiée Windows :
- Démarrage automatique au boot
- Pas d'intervention nécessaire
- Redémarrage automatique après crash (si configuré)

---

## 🛠️ Dépannage

### Flask ne démarre pas

1. **Vérifier l'environnement virtuel:**
   ```powershell
   Test-Path C:\Apps\venv\Scripts\activate.ps1
   ```

2. **Vérifier Python:**
   ```powershell
   python --version
   ```

3. **Vérifier les dépendances:**
   ```powershell
   cd C:\Apps
   .\venv\Scripts\activate.ps1
   pip list
   ```

### Flask démarre mais ne répond pas

1. **Vérifier le port 5000:**
   ```powershell
   netstat -ano | findstr :5000
   ```

2. **Vérifier les logs Flask:**
   - Regardez la fenêtre PowerShell où Flask tourne
   - Recherchez les messages d'erreur

3. **Tester manuellement:**
   ```powershell
   curl.exe http://localhost:5000
   ```

### Processus Flask multiples

Si plusieurs instances de Flask tournent :

```powershell
# Voir tous les processus Python
Get-Process python

# Arrêter tous les processus Flask
Get-Process python | Where-Object {$_.CommandLine -like "*app.py*"} | Stop-Process -Force
```

---

## 📝 Notes Importantes

1. **Environnement virtuel requis:**
   - Les scripts cherchent `venv` dans le répertoire `C:\Apps`
   - Si vous utilisez un autre nom, modifiez les scripts

2. **Port par défaut:**
   - Flask démarre sur le port 5000
   - Si le port est occupé, modifiez `app.py`

3. **Watchdog:**
   - Les scripts utilisent `run_flask_with_watchdog.py` si disponible
   - Sinon, ils utilisent `app.py` directement

4. **Permissions:**
   - Les scripts PowerShell peuvent nécessiter d'autoriser l'exécution:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

---

## 🎯 Exemples d'Utilisation

### Démarrage rapide (développement)
```powershell
cd C:\Apps
.\demarrer_flask_auto.ps1
```

### Créer une tâche pour démarrage au boot
```powershell
# En tant qu'administrateur
cd C:\Apps
.\creer_tache_planifiee_flask.ps1
# Choisir option 1 (Au démarrage de Windows)
```

### Démarrage via raccourci Windows
1. Créer un raccourci vers `demarrer_flask_auto.bat`
2. Placer le raccourci sur le bureau
3. Double-cliquer pour démarrer Flask

---

## ✅ Vérification du Démarrage

Après le démarrage, vérifiez que Flask fonctionne :

```powershell
# Test simple
curl.exe http://localhost:5000

# Test avec vérification du statut
Invoke-WebRequest -Uri http://localhost:5000 -UseBasicParsing
```

Si vous obtenez une réponse HTTP 200, Flask fonctionne correctement ! 🎉
