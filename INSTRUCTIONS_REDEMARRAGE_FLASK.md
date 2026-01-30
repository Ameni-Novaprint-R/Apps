# Instructions pour redémarrer Flask et activer les boutons d'export

## Problème
Les boutons "Export Excel" et "Export PDF" n'apparaissent pas car Flask n'a pas rechargé les nouvelles routes et templates.

## Solution rapide

### Option 1 : Script automatique (recommandé)
Double-cliquez sur :
```
c:\Apps\redemarrer_flask_et_verifier.bat
```

### Option 2 : Redémarrage manuel

1. **Arrêter Flask**
   - Dans la console où Flask tourne, appuyez sur `Ctrl+C`
   - Ou fermez la fenêtre de console

2. **Redémarrer Flask**
   ```powershell
   cd C:\Apps
   python app.py
   ```
   
   Ou si vous utilisez watchdog :
   ```powershell
   python run_flask_with_watchdog.py
   ```

3. **Vérifier que les boutons apparaissent**
   - Ouvrez : http://localhost:5000/projet11/statistiques
   - Les boutons "Export Excel" (vert) et "Export PDF" (rouge) doivent apparaître à côté de "Liste des traitements"

## Vérification

Après redémarrage, testez les routes :
- http://localhost:5000/projet11/statistiques/export-excel (doit télécharger un fichier Excel)
- http://localhost:5000/projet11/statistiques/export-pdf (doit télécharger un fichier PDF)

## Note importante

Les bibliothèques nécessaires sont maintenant installées :
- ✅ pandas
- ✅ openpyxl  
- ✅ reportlab

Les routes d'export devraient fonctionner correctement après le redémarrage de Flask.
