# Solution pour exécuter les SQL depuis Cursor (sans désactiver le sandbox)

## Problème

Le sandbox de Cursor **refuse catégoriquement** d'exécuter des commandes quand Cursor est détecté comme "élevé" (mode admin), même avec `required_permissions: ['network']`. Il n'existe **pas de moyen de contourner** cette restriction sans désactiver le sandbox.

## Solution pratique : Script automatique

Un script **`Lancer_Init_Web_Tables_Auto.bat`** a été créé pour automatiser l'exécution :

### Utilisation

1. **Double-clic** sur **`c:\Apps\Lancer_Init_Web_Tables_Auto.bat`**
2. Le script :
   - Vérifie si l'app Flask tourne déjà
   - Lance `python app.py` en arrière-plan si nécessaire
   - Ouvre automatiquement le navigateur sur **http://localhost:5000/admin/init-web-tables**
3. Les scripts SQL s'exécutent automatiquement sur la page
4. Vous voyez le résultat directement dans le navigateur

### Avantages

- ✅ **Sandbox conservé** : pas besoin de désactiver le sandbox
- ✅ **Automatique** : un double-clic suffit
- ✅ **Résultat visible** : succès/erreur affiché dans le navigateur
- ✅ **Fonctionne même si Cursor est en admin** : les scripts s'exécutent dans le processus Flask, pas dans Cursor

## Alternative : Depuis Cursor (si l'app Flask tourne déjà)

Si l'app Flask est déjà en cours d'exécution (dans une autre fenêtre PowerShell), vous pouvez simplement :

1. Ouvrir le navigateur manuellement
2. Aller sur : **http://localhost:5000/admin/init-web-tables**

## Pourquoi cette solution ?

Le sandbox de Cursor est conçu pour **bloquer toute exécution** quand le processus parent est élevé, pour des raisons de sécurité. C'est une limitation **intentionnelle** de Cursor, pas un bug. La seule façon de contourner serait de désactiver le sandbox, ce que vous refusez (et c'est une bonne décision de sécurité).

La route web fonctionne car :
- Les scripts s'exécutent dans le **processus Python de l'app Flask**
- Ce processus n'est **pas** dans le sandbox Cursor
- Il peut donc s'exécuter même si Cursor est en admin

## Résumé

| Méthode | Action |
|---------|--------|
| **Script automatique** | Double-clic sur `Lancer_Init_Web_Tables_Auto.bat` → tout se fait automatiquement |
| **Manuel** | `python app.py` dans PowerShell → navigateur → `http://localhost:5000/admin/init-web-tables` |
