# Redémarrer Flask pour activer les boutons d'export

## Problème
Les boutons "Export Excel" et "Export PDF" n'apparaissent pas car Flask n'a pas rechargé les nouvelles routes.

## Solution

### Option 1 : Redémarrer Flask manuellement
1. Arrêtez Flask (Ctrl+C dans la console où Flask tourne)
2. Redémarrez Flask :
   ```powershell
   cd C:\Apps
   python app.py
   ```
   OU si vous utilisez watchdog :
   ```powershell
   python run_flask_with_watchdog.py
   ```

### Option 2 : Forcer le rechargement via watchdog
Si Flask tourne avec watchdog, modifiez légèrement le fichier `routes/projet11_routes.py` (ajoutez un espace) pour déclencher le rechargement automatique.

### Option 3 : Vider le cache Python
```powershell
cd C:\Apps
Get-ChildItem -Path . -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Recurse -Filter "*.pyc" | Remove-Item -Force
```
Puis redémarrez Flask.

## Vérification
Après redémarrage, vérifiez que les routes fonctionnent :
- http://localhost:5000/projet11/statistiques/export-excel (doit télécharger un fichier Excel)
- http://localhost:5000/projet11/statistiques/export-pdf (doit télécharger un fichier PDF)

Les boutons doivent apparaître sur la page :
- http://localhost:5000/projet11/statistiques
