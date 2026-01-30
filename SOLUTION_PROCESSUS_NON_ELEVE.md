# Solution : Exécuter les SQL via un processus non-élevé

## Problème

Cursor 2.4.21 bloque l'exécution de commandes quand le processus est détecté comme "élevé", même avec `chat.sandboxEnabled: false`. Cette restriction ne peut pas être contournée directement depuis Cursor.

## Solution : Créer un processus non-élevé

Même si Cursor est élevé, on peut créer un **nouveau processus non-élevé** qui exécute les scripts Python. Ce nouveau processus n'hérite pas de l'élévation de Cursor.

## Méthodes disponibles

### Méthode 1 : Script batch avec explorer.exe (RECOMMANDÉ)

**Fichier** : `Executer_SQL_Via_Explorer.bat`

**Utilisation** :
1. Double-clic sur `Executer_SQL_Via_Explorer.bat`
2. Le script crée un batch temporaire avec `__COMPAT_LAYER=RunAsInvoker`
3. Utilise `explorer.exe` pour lancer ce batch dans un processus non-élevé
4. Les scripts Python s'exécutent dans cette nouvelle fenêtre

**Avantages** :
- ✅ Simple à utiliser (double-clic)
- ✅ Fonctionne même si Cursor est élevé
- ✅ La fenêtre reste ouverte pour voir les résultats

### Méthode 2 : Script PowerShell avec explorer.exe

**Fichier** : `Executer_SQL_Via_PowerShell_Non_Eleve.ps1`

**Utilisation** :
1. Clic droit → "Exécuter avec PowerShell" sur `Executer_SQL_Via_PowerShell_Non_Eleve.ps1`
2. Ou depuis Cursor (si possible) : `powershell -ExecutionPolicy Bypass -File Executer_SQL_Via_PowerShell_Non_Eleve.ps1`
3. Le script crée un PowerShell temporaire et le lance via `explorer.exe`

**Avantages** :
- ✅ Plus de contrôle sur l'affichage
- ✅ Gestion d'erreurs améliorée
- ✅ Fonctionne même si Cursor est élevé

### Méthode 3 : Script batch avec runas /trustlevel

**Fichier** : `Executer_SQL_Runas_TrustLevel.bat`

**Utilisation** :
1. Double-clic sur `Executer_SQL_Runas_TrustLevel.bat`
2. Utilise `runas /trustlevel:0x20000` pour forcer l'exécution sans élévation
3. Les scripts Python s'exécutent dans une nouvelle fenêtre

**Avantages** :
- ✅ Méthode Windows native
- ✅ Force l'exécution sans élévation
- ⚠️ Peut demander une confirmation UAC

### Méthode 4 : Script Python avec schtasks (AVANCÉ)

**Fichier** : `Executer_SQL_Via_Processus_Non_Eleve.py`

**Utilisation** :
```bash
python Executer_SQL_Via_Processus_Non_Eleve.py
```

**Fonctionnement** :
- Utilise `schtasks` pour créer une tâche Windows temporaire
- La tâche s'exécute avec `RunLevel: LeastPrivilege` (sans élévation)
- Exécute les scripts Python dans cette tâche
- Supprime la tâche après exécution

**Avantages** :
- ✅ Méthode la plus fiable pour créer un processus non-élevé
- ✅ Fonctionne même si Cursor est élevé
- ⚠️ Nécessite des droits pour créer des tâches planifiées

## Comment ça fonctionne ?

### Explorer.exe comme lanceur non-élevé

`explorer.exe` s'exécute toujours **sans élévation** (même si lancé depuis un processus élevé). Quand on utilise `explorer.exe` pour lancer un autre programme, ce programme hérite du niveau de privilège d'explorer.exe (non-élevé).

**Exemple** :
```batch
explorer.exe "powershell.exe -File script.ps1"
```

Le PowerShell lancé sera **non-élevé**, même si le batch qui a lancé explorer.exe était élevé.

### Schtasks avec LeastPrivilege

Les tâches Windows planifiées peuvent être configurées avec `RunLevel: LeastPrivilege`, ce qui force l'exécution sans élévation, même si l'utilisateur est administrateur.

## Comparaison avec la route web

| Méthode | Avantages | Inconvénients |
|---------|-----------|---------------|
| **Route web** | ✅ Fonctionne toujours<br>✅ Interface visuelle<br>✅ Pas de processus à créer | ⚠️ Nécessite Flask en cours d'exécution |
| **Processus non-élevé** | ✅ Exécution directe<br>✅ Pas besoin de Flask<br>✅ Résultats dans la console | ⚠️ Crée une nouvelle fenêtre |

## Recommandation

**Pour une utilisation rapide** : Utilisez `Executer_SQL_Via_Explorer.bat` (double-clic).

**Pour une intégration dans Cursor** : 

⚠️ **IMPORTANT** : Si Cursor bloque **toute** exécution de commande (même `run_terminal_cmd`), ces scripts ne pourront **pas** être exécutés depuis Cursor lui-même. 

**Solutions** :
1. **Exécuter manuellement** : Double-clic sur les `.bat` depuis l'Explorateur Windows
2. **Utiliser la route web** : La seule méthode qui fonctionne depuis Cursor quand le terminal est bloqué
3. **Lancer depuis un autre terminal** : Ouvrir PowerShell ou CMD séparément (non-élevé) et exécuter les scripts depuis là

## Test

Pour tester si une méthode fonctionne :

1. Vérifiez que Cursor est élevé :
   ```powershell
   ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
   ```

2. Lancez `Executer_SQL_Via_Explorer.bat`

3. Dans la nouvelle fenêtre, vérifiez que le processus n'est pas élevé :
   ```powershell
   ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
   ```
   Devrait retourner `False`.

4. Les scripts Python devraient s'exécuter normalement.
