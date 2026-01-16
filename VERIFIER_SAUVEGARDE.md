# Instructions pour Vérifier la Sauvegarde de CtRel

## Ce qu'il faut faire maintenant

Les logs que vous avez partagés montrent uniquement les appels GET (récupération des services). Pour diagnostiquer le problème de `ct_rel`, nous avons besoin de voir les logs de **sauvegarde** (POST).

## Étapes à suivre

### 1. Ouvrir la console Flask
- Gardez la console Flask ouverte et visible
- Assurez-vous de voir les dernières lignes

### 2. Ouvrir la console du navigateur
- Appuyez sur **F12** dans le navigateur
- Allez dans l'onglet **Console**

### 3. Créer un nouveau dossier avec CtRel

1. Sur la page Projet 19, cliquez sur **"➕ Nouveau dossier"**
2. Sélectionnez un numéro de dossier (ex: `2025050176`)
3. **Cochez quelques services** pour que le coût total soit > 0
4. Vérifiez que **"Coût Total Réel"** s'affiche avec une valeur (ex: `511,xxx`)
5. Cliquez sur **"💾 Enregistrer"**

### 4. Copier les logs Flask

**Immédiatement après avoir cliqué sur "Enregistrer"**, dans la console Flask, vous devriez voir des logs qui commencent par :

```
[DEBUG api_create_dossier] ct_rel reçu: ...
[DEBUG api_create_dossier] ct_rel converti: ...
[DEBUG create_web_s_dos_encours] [OK] Ajout de CtRel=...
[DEBUG create_web_s_dos_encours] Colonnes: ...
[DEBUG create_web_s_dos_encours] Valeurs: ...
[DEBUG create_web_s_dos_encours] [OK] Verification apres INSERT: CtRel enregistre = ...
```

**Copiez TOUS ces logs** et partagez-les avec moi.

### 5. Copier les logs du navigateur

Dans la console du navigateur, vous devriez voir :

```
[saveNewDossierFromPopup] ctRelText depuis DOM: ...
[saveNewDossierFromPopup] ctRelText parsé: ...
[saveNewDossierFromPopup] Valeurs à sauvegarder: ...
[saveNewDossierFromPopup] Payload JSON à envoyer: ...
```

**Copiez TOUS ces logs** également.

## Ce que je cherche

Je veux vérifier :
1. ✅ Que `ctRel` est bien calculé dans le popup (console navigateur)
2. ✅ Que `ctRel` est bien envoyé dans le JSON (console navigateur)
3. ✅ Que `ctRel` est bien reçu par l'API Flask (console Flask)
4. ✅ Que `ctRel` est bien enregistré dans la base (console Flask)
5. ✅ Que `ctRel` est bien récupéré depuis la base (console Flask)

## Si vous ne voyez pas ces logs

Si vous ne voyez **aucun** log commençant par `[DEBUG api_create_dossier]` ou `[saveNewDossierFromPopup]`, cela signifie que :
- Soit les logs ne sont pas activés (mais ils devraient l'être)
- Soit il y a une erreur avant d'arriver à ces fonctions

Dans ce cas, vérifiez s'il y a des **erreurs** (en rouge) dans la console Flask ou du navigateur.
