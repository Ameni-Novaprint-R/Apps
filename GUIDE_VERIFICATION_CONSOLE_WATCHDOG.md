# Guide : Comment Vérifier le Statut 200 dans la Console Watchdog

## 📋 Étape 1 : Localiser la Console Watchdog

### Où trouver la console ?
La console Watchdog est la fenêtre de terminal où vous avez lancé :
- `run-flask-watchdog.bat` (double-clic)
- `run-flask-watchdog.ps1` (PowerShell)
- `python run_flask_with_watchdog.py` (ligne de commande)

### À quoi ressemble la console Watchdog ?
Vous devriez voir quelque chose comme :
```
================================================================================
FLASK AVEC WATCHDOG - Rechargement automatique
================================================================================
Répertoire surveillé: C:\Apps
Extensions surveillées: .py, .html, .js, .css, .sql
Répertoires exclus: __pycache__, .git, venv, .venv, node_modules, .cursor
================================================================================

Appuyez sur Ctrl+C pour arrêter

[WATCHDOG] Démarrage de Flask...
[WATCHDOG] Flask démarré (PID: 12345)
[WATCHDOG] Surveillance des fichiers activée

Projet18 blueprint enregistre
Projet19 blueprint enregistre - 9 routes
Projet20 blueprint enregistre - 3 routes
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.10.225:5000
```

---

## 📋 Étape 2 : Comprendre les Messages Flask

### Messages Normaux (Démarrage)
Quand Flask démarre, vous voyez :
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### Messages de Requête HTTP
Chaque fois qu'une page est chargée, Flask affiche une ligne comme :
```
127.0.0.1 - - [20/Oct/2025 15:30:45] "GET / HTTP/1.1" 200 -
```

**Format de la ligne :**
```
[IP] - - [DATE/HEURE] "METHODE URL PROTOCOLE" CODE_STATUT -
```

**Exemples :**
- ✅ `"GET / HTTP/1.1" 200` = Succès (page chargée)
- ❌ `"GET / HTTP/1.1" 500` = Erreur serveur
- ⚠️ `"GET / HTTP/1.1" 404` = Page non trouvée
- 🔄 `"GET / HTTP/1.1" 302` = Redirection

---

## 📋 Étape 3 : Vérifier le Statut 200

### Méthode 1 : Test Simple dans le Navigateur

1. **Ouvrez votre navigateur**
2. **Accédez à** : `http://127.0.0.1:5000/`
3. **Regardez IMMÉDIATEMENT la console Watchdog**

### Ce que vous devriez voir (SUCCÈS) :
```
127.0.0.1 - - [20/Oct/2025 15:30:45] "GET / HTTP/1.1" 200 -
```
✅ **Le nombre 200** confirme que la page s'est chargée avec succès !

### Ce que vous NE devriez PAS voir (ERREUR) :
```
127.0.0.1 - - [20/Oct/2025 15:30:45] "GET / HTTP/1.1" 500 -
Traceback (most recent call last):
  File "C:\Apps\app.py", line 84, in index
    ...
[ERREUR] Message d'erreur
```
❌ **Le nombre 500** indique une erreur serveur

---

## 📋 Étape 4 : Exemples Visuels

### ✅ Exemple de Console avec Succès (Statut 200)

```
[WATCHDOG] Surveillance des fichiers activée

 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 123-456-789

127.0.0.1 - - [20/Oct/2025 15:30:45] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [20/Oct/2025 15:30:50] "GET /projet20/ HTTP/1.1" 200 -
127.0.0.1 - - [20/Oct/2025 15:31:02] "GET /projet19/ HTTP/1.1" 200 -
```

**✅ Tous les statuts sont 200 = Tout fonctionne !**

---

### ❌ Exemple de Console avec Erreur (Statut 500)

```
127.0.0.1 - - [20/Oct/2025 15:30:45] "GET / HTTP/1.1" 500 -
Traceback (most recent call last):
  File "C:\Apps\templates\base.html", line 38, in top-level template code
    <li><a href="{{ url_for('projet20.index') }}">🔍 Analyse Dossiers</a></li>
    ^^^^^^^^^
werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'projet20.index'
```

**❌ Le statut 500 + Traceback = Erreur à corriger**

---

## 📋 Étape 5 : Messages Watchdog lors des Modifications

### Quand vous modifiez un fichier :
```
================================================================================
[WATCHDOG] Fichier modifié: C:\Apps\templates\base.html
[WATCHDOG] Redémarrage de Flask...
================================================================================
[WATCHDOG] Nettoyage du cache Python...
[WATCHDOG] 5 fichier(s) .pyc supprimé(s)
[WATCHDOG] Démarrage de Flask...
[WATCHDOG] Flask démarré (PID: 12346)

Projet18 blueprint enregistre
Projet19 blueprint enregistre - 9 routes
Projet20 blueprint enregistre - 3 routes
 * Serving Flask app 'app'
 * Debug mode: on
```

**✅ Watchdog a détecté la modification et redémarré Flask automatiquement**

---

## 📋 Étape 6 : Vérification Rapide (Checklist)

### ✅ Checklist de Vérification

- [ ] **Console Watchdog ouverte et visible**
- [ ] **Flask démarré** (vous voyez "Running on http://127.0.0.1:5000")
- [ ] **Accès à** `http://127.0.0.1:5000/` dans le navigateur
- [ ] **Regardez la console** immédiatement après le chargement
- [ ] **Vérifiez le code de statut** :
  - ✅ **200** = Succès (page chargée correctement)
  - ❌ **500** = Erreur serveur (problème à résoudre)
  - ⚠️ **404** = Page non trouvée
  - 🔄 **302** = Redirection (normal pour certaines pages)

---

## 📋 Étape 7 : Commandes Utiles

### Voir les Dernières Lignes de la Console
Si la console est trop longue, utilisez :
```powershell
# Dans PowerShell, vous pouvez faire défiler vers le bas
# ou utiliser Ctrl+End pour aller à la fin
```

### Filtrer les Requêtes 200
Dans la console, cherchez les lignes contenant "200" :
- Windows : Utilisez Ctrl+F et cherchez "200"
- Vous verrez toutes les requêtes réussies

### Filtrer les Erreurs 500
Cherchez "500" dans la console :
- Vous verrez toutes les erreurs serveur

---

## 💡 Astuces

### Astuce 1 : Garder la Console Visible
- Placez la console Watchdog à côté de votre navigateur
- Vous verrez les requêtes en temps réel

### Astuce 2 : Vérifier Après Chaque Modification
- Après chaque modification de code
- Watchdog redémarre Flask automatiquement
- Testez immédiatement pour voir le statut

### Astuce 3 : Comprendre les Codes de Statut
- **200** = OK (tout va bien)
- **201** = Créé (ressource créée avec succès)
- **302** = Redirection (normal)
- **400** = Mauvaise requête (erreur côté client)
- **404** = Non trouvé (URL incorrecte)
- **500** = Erreur serveur (problème dans le code)
- **502** = Bad Gateway (problème de proxy)
- **503** = Service indisponible

---

## 🎯 Résumé Rapide

**Pour vérifier le statut 200 :**

1. ✅ Ouvrez la console Watchdog
2. ✅ Accédez à `http://127.0.0.1:5000/` dans votre navigateur
3. ✅ Regardez la console Watchdog
4. ✅ Cherchez la ligne : `"GET / HTTP/1.1" 200 -`
5. ✅ Si vous voyez **200** = ✅ Succès !
6. ✅ Si vous voyez **500** = ❌ Erreur (regardez le traceback en dessous)

---

## 📞 En Cas de Problème

Si vous voyez toujours un statut 500 :

1. **Copiez le message d'erreur complet** de la console
2. **Copiez le traceback** (toutes les lignes d'erreur)
3. **Partagez-les avec moi** pour diagnostic

Les erreurs apparaissent généralement juste après la ligne avec le statut 500.
