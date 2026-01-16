# Commandes pour vérifier que les __pycache__ du projet 19 sont supprimés

## 🎯 Objectif
Vérifier que tous les fichiers `__pycache__` liés au projet 19 ont bien été supprimés.

## 🔧 Méthode 1 : Utiliser le script de vérification (RECOMMANDÉ)

### Étape 1 : Ouvrir une Invite de commandes (CMD)
```cmd
cd C:\Apps
```

### Étape 2 : Exécuter le script
```cmd
verifier_cache_projet19.bat
```

Le script affichera :
- ✅ **[OK]** si les fichiers ont été supprimés
- ❌ **[ERREUR]** si des fichiers existent encore
- ⚠️ **[ATTENTION]** si les dossiers `__pycache__` existent mais ne contiennent pas de fichiers projet19

## 🔧 Méthode 2 : Commandes manuelles (CMD)

### Vérifier routes\__pycache__
```cmd
cd C:\Apps

REM Vérifier si le dossier existe
if exist "routes\__pycache__" (
    echo Le dossier routes\__pycache__ existe encore!
    dir /b "routes\__pycache__"
    
    REM Chercher les fichiers projet19
    dir /b "routes\__pycache__" | findstr /i "projet19"
    if %ERRORLEVEL% EQU 0 (
        echo [ERREUR] Fichiers projet19 trouves!
    ) else (
        echo [OK] Aucun fichier projet19 trouve
    )
) else (
    echo [OK] routes\__pycache__ n'existe pas - Supprime
)
```

### Vérifier __pycache__ à la racine
```cmd
cd C:\Apps

REM Vérifier si le dossier existe
if exist "__pycache__" (
    echo Le dossier __pycache__ existe encore!
    dir /b "__pycache__"
    
    REM Chercher db.cpython-*.pyc (utilisé par projet19)
    dir /b "__pycache__\db.cpython-*.pyc" 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo [ERREUR] db.cpython-*.pyc existe encore!
    ) else (
        echo [OK] db.cpython-*.pyc n'existe pas
    )
) else (
    echo [OK] __pycache__ n'existe pas - Supprime
)
```

### Recherche globale de fichiers projet19
```cmd
cd C:\Apps

REM Chercher tous les fichiers .pyc contenant "projet19"
dir /s /b *projet19*.pyc 2>nul

if %ERRORLEVEL% EQU 0 (
    echo [ERREUR] Des fichiers projet19.pyc existent encore!
) else (
    echo [OK] Aucun fichier projet19.pyc trouve
)
```

## 🔧 Méthode 3 : Commandes PowerShell

### Vérification complète
```powershell
cd C:\Apps

Write-Host "[1] Verification de routes\__pycache__..." -ForegroundColor Yellow
if (Test-Path "routes\__pycache__") {
    Write-Host "[ATTENTION] routes\__pycache__ existe encore!" -ForegroundColor Yellow
    $projet19Files = Get-ChildItem "routes\__pycache__" -Filter "*projet19*" -ErrorAction SilentlyContinue
    if ($projet19Files) {
        Write-Host "[ERREUR] Fichiers projet19 trouves:" -ForegroundColor Red
        $projet19Files | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Red }
    } else {
        Write-Host "[OK] Aucun fichier projet19 trouve" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] routes\__pycache__ n'existe pas" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2] Verification de __pycache__ a la racine..." -ForegroundColor Yellow
if (Test-Path "__pycache__") {
    Write-Host "[ATTENTION] __pycache__ existe encore!" -ForegroundColor Yellow
    $dbFiles = Get-ChildItem "__pycache__" -Filter "db.cpython-*.pyc" -ErrorAction SilentlyContinue
    if ($dbFiles) {
        Write-Host "[ERREUR] db.cpython-*.pyc existe encore:" -ForegroundColor Red
        $dbFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Red }
    } else {
        Write-Host "[OK] db.cpython-*.pyc n'existe pas" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] __pycache__ n'existe pas" -ForegroundColor Green
}

Write-Host ""
Write-Host "[3] Recherche globale..." -ForegroundColor Yellow
$allProjet19Files = Get-ChildItem -Path . -Recurse -Filter "*projet19*.pyc" -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike "*\venv\*" }
if ($allProjet19Files) {
    Write-Host "[ERREUR] Fichiers projet19.pyc trouves:" -ForegroundColor Red
    $allProjet19Files | ForEach-Object { Write-Host "  - $($_.FullName)" -ForegroundColor Red }
} else {
    Write-Host "[OK] Aucun fichier projet19.pyc trouve" -ForegroundColor Green
}
```

## 📋 Ce qu'il faut vérifier

### ✅ Résultat attendu (SUCCÈS)
- `routes\__pycache__` n'existe **PAS** OU ne contient **PAS** de fichiers contenant "projet19"
- `__pycache__` à la racine n'existe **PAS** OU ne contient **PAS** `db.cpython-*.pyc`
- Aucun fichier `*projet19*.pyc` trouvé dans le projet (sauf dans `venv\`)

### ❌ Résultat indésirable (ERREUR)
- `routes\__pycache__\*projet19*.pyc` existe encore
- `__pycache__\db.cpython-*.pyc` existe encore
- Des fichiers `.pyc` contenant "projet19" sont trouvés ailleurs

## 🔄 Que faire si des fichiers existent encore ?

1. **Relancer le script de nettoyage** :
   ```cmd
   nettoyer_cache_projet19_complet.bat
   ```

2. **Vérifier à nouveau** :
   ```cmd
   verifier_cache_projet19.bat
   ```

3. **Si nécessaire, supprimer manuellement** :
   ```cmd
   rmdir /s /q "routes\__pycache__"
   rmdir /s /q "__pycache__"
   ```

## ⚠️ Note importante

- Les fichiers dans `venv\__pycache__` peuvent être ignorés (c'est l'environnement virtuel)
- Les autres projets (projet11, projet12, etc.) peuvent avoir leurs propres `__pycache__` - c'est normal
