# Instructions : Comment exécuter les scripts .bat

## ❌ ERREUR COMMUNE À ÉVITER

**NE PAS copier-coller le contenu du fichier `.bat` dans la console CMD !**

Si vous faites cela, CMD interprète chaque ligne individuellement au lieu d'exécuter le script, ce qui cause des erreurs comme :
- `%%f était inattendu`
- `Plus ?` (CMD attend plus de commandes)
- Des erreurs de syntaxe

## ✅ MÉTHODE CORRECTE

### Option 1 : Exécuter depuis l'Explorateur Windows

1. **Ouvrez l'Explorateur Windows** (Win + E)
2. **Naviguez vers** `C:\Apps`
3. **Trouvez le fichier** `verifier_cache_projet19_simple.bat`
4. **Double-cliquez** sur le fichier

Le script s'exécutera automatiquement dans une fenêtre CMD.

### Option 2 : Exécuter depuis CMD

1. **Ouvrez une Invite de commandes (CMD)**
   - Appuyez sur `Win + R`
   - Tapez `cmd` et appuyez sur `Entrée`

2. **Naviguez vers le répertoire du projet**
   ```cmd
   cd C:\Apps
   ```

3. **Exécutez le script**
   ```cmd
   verifier_cache_projet19_simple.bat
   ```
   
   **OU** (si vous êtes dans un autre répertoire)
   ```cmd
   C:\Apps\verifier_cache_projet19_simple.bat
   ```

### Option 3 : Depuis PowerShell

1. **Ouvrez PowerShell**
   - Clic droit sur le menu Démarrer → **Windows PowerShell**

2. **Naviguez vers le répertoire du projet**
   ```powershell
   cd C:\Apps
   ```

3. **Exécutez le script**
   ```powershell
   .\verifier_cache_projet19_simple.bat
   ```

## 📋 Résumé des scripts disponibles

### Scripts de nettoyage
- `nettoyer_cache_projet19_complet.bat` - Supprime TOUS les `__pycache__` du projet 19

### Scripts de vérification
- `verifier_cache_projet19_simple.bat` - Vérifie que les `__pycache__` sont supprimés

## ⚠️ IMPORTANT

- **Toujours exécuter depuis** `C:\Apps` (ou fournir le chemin complet)
- **Ne jamais copier-coller le contenu** du fichier `.bat` dans CMD
- **Exécuter le fichier directement** en double-cliquant ou en tapant son nom

## 🔍 Vérification rapide

Pour vérifier rapidement que vous êtes dans le bon répertoire :

```cmd
cd
```

Cela doit afficher : `C:\Apps`

Sinon, exécutez :
```cmd
cd C:\Apps
```
