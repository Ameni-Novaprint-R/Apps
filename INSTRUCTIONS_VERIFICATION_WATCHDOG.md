# Instructions pour Vérifier les Logs Flask avec Watchdog

## 📋 Méthode 1 : Console Watchdog (RECOMMANDÉE)

### Étape 1 : Localiser la Console Watchdog
1. Trouvez la fenêtre de console où vous avez lancé :
   - `run-flask-watchdog.bat` OU
   - `run-flask-watchdog.ps1` OU
   - `python run_flask_with_watchdog.py`

### Étape 2 : Observer les Logs en Temps Réel
Dans cette console, vous verrez :
- ✅ Les messages de démarrage de Flask
- ✅ Toutes les requêtes HTTP avec leur statut
- ✅ Les erreurs Python complètes avec traceback
- ✅ Les messages `[WATCHDOG]` lors des rechargements

### Étape 3 : Reproduire l'Erreur
1. Gardez la console Watchdog ouverte et visible
2. Accédez à `http://127.0.0.1:5000/` dans votre navigateur
3. **Immédiatement** regardez la console Watchdog
4. Vous devriez voir l'erreur complète avec le traceback

---

## 📋 Méthode 2 : Fichier de Log d'Erreurs

### Localisation
```
C:\Apps\.cursor\flask_errors.log
```

### Comment Vérifier
1. Ouvrez ce fichier avec un éditeur de texte
2. Les erreurs sont enregistrées avec :
   - Date et heure
   - Message d'erreur
   - Traceback complet

### Commande PowerShell pour Voir les Dernières Erreurs
```powershell
Get-Content C:\Apps\.cursor\flask_errors.log -Tail 50
```

---

## 📋 Méthode 3 : Script de Test Automatique

### Utiliser le Script de Test
```powershell
cd C:\Apps
.\venv\Scripts\activate
python verifier_erreur_500.py
```

Ce script va :
- ✅ Tester la route principale
- ✅ Afficher le statut HTTP
- ✅ Afficher le contenu de l'erreur si disponible
- ✅ Donner des instructions détaillées

---

## 🔍 Ce que Vous Devriez Voir dans les Logs

### Exemple de Log Normal (Succès)
```
127.0.0.1 - - [20/Oct/2025 15:21:54] "GET / HTTP/1.1" 200 -
```

### Exemple de Log avec Erreur 500
```
127.0.0.1 - - [20/Oct/2025 15:21:54] "GET / HTTP/1.1" 500 -
Traceback (most recent call last):
  File "C:\Apps\app.py", line 84, in index
    return render_template("index.html")
  ...
[ERREUR] Message d'erreur détaillé ici
```

---

## ⚠️ Si Vous Ne Voyez Pas les Logs

### Problème : Console Watchdog Fermée
**Solution :**
1. Relancez Watchdog :
   ```powershell
   cd C:\Apps
   .\run-flask-watchdog.ps1
   ```
2. Gardez cette console ouverte

### Problème : Flask Ne Redémarre Pas
**Solution :**
1. Vérifiez que Watchdog surveille bien les fichiers
2. Vous devriez voir `[WATCHDOG] Surveillance des fichiers activée`
3. Si nécessaire, redémarrez Watchdog manuellement

### Problème : Aucune Erreur dans les Logs
**Solution :**
1. Vérifiez que Flask tourne bien (port 5000)
2. Testez avec le script `verifier_erreur_500.py`
3. Vérifiez le fichier `C:\Apps\.cursor\flask_errors.log`

---

## 📝 Informations à Me Fournir

Si l'erreur persiste, copiez-moi :

1. **Le message d'erreur complet** de la console Watchdog
2. **Le traceback complet** (toutes les lignes)
3. **Les dernières lignes** du fichier `flask_errors.log`
4. **Le résultat** du script `verifier_erreur_500.py`

---

## 🚀 Démarrage Rapide

```powershell
# 1. Aller dans le répertoire
cd C:\Apps

# 2. Activer l'environnement virtuel
.\venv\Scripts\activate

# 3. Lancer Watchdog (dans une console)
python run_flask_with_watchdog.py

# 4. Dans une AUTRE console, tester l'erreur
python verifier_erreur_500.py

# 5. Regarder la console Watchdog pour voir l'erreur
```

---

## 💡 Astuce

Pour voir les logs en continu dans PowerShell :
```powershell
Get-Content C:\Apps\.cursor\flask_errors.log -Wait -Tail 20
```
(Cela affiche les 20 dernières lignes et attend les nouvelles erreurs)
