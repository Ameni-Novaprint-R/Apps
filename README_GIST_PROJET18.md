# Publication du Projet 18 sur GitHub Gist

Ce guide explique comment publier le Projet 18 (Agenda Semainier 2026) sur GitHub Gist.

## Fichiers du Projet 18

Le projet 18 comprend les fichiers suivants :
- `routes/projet18_routes.py` - Routes Flask et génération PDF
- `logic/projet18.py` - Logique métier (semaines, jours fériés)
- `templates/projet18.html` - Template HTML

## Prérequis

1. Un compte GitHub
2. Un token d'accès GitHub avec les permissions `gist`

## Création d'un token GitHub

1. Allez sur https://github.com/settings/tokens
2. Cliquez sur **"Generate new token (classic)"**
3. Donnez un nom au token (ex: "Gist Projet 18")
4. Cochez la case **"gist"** dans les permissions
5. Cliquez sur **"Generate token"**
6. **Copiez le token** (vous ne pourrez plus le voir après)

## Utilisation des scripts

### Option 1 : Script avec requests (recommandé)

```powershell
python create_gist_projet18.py
```

### Option 2 : Script avec bibliothèque standard uniquement

```powershell
python create_gist_projet18_simple.py
```

## Configuration du token

### Méthode 1 : Variable d'environnement (recommandé)

**Windows PowerShell:**
```powershell
$env:GITHUB_TOKEN='votre_token_ici'
python create_gist_projet18.py
```

**Windows CMD:**
```cmd
set GITHUB_TOKEN=votre_token_ici
python create_gist_projet18.py
```

### Méthode 2 : Saisie interactive

Lancez simplement le script et entrez le token quand il vous est demandé :
```powershell
python create_gist_projet18.py
```

## Résultat

Le script créera un Gist avec :
- Une description du projet
- Les 3 fichiers du projet 18
- Un lien URL vers le Gist créé

Vous pourrez ensuite partager ce lien avec d'autres personnes.

## Notes

- Les Gists peuvent être **publics** (visibles par tous) ou **secrets** (accessibles uniquement via le lien)
- Les Gists publics apparaissent dans votre profil GitHub
- Vous pouvez modifier ou supprimer le Gist depuis l'interface GitHub











