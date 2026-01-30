# Créer le Dépôt GitHub et Synchroniser

## Étape 1 : Créer le Dépôt sur GitHub

1. **Connectez-vous à GitHub** : https://github.com
   - Email : ameni.compta@novaprint.tn
   - Mot de passe : @menI123**

2. **Créer un nouveau dépôt** :
   - Cliquez sur le bouton "+" en haut à droite
   - Sélectionnez "New repository"
   - **Nom du dépôt** : `Apps`
   - **Description** : (optionnel) "Applications Novaprint"
   - **Visibilité** : Private (recommandé) ou Public
   - **NE COCHEZ PAS** "Add a README file" (le dépôt local a déjà des fichiers)
   - **NE COCHEZ PAS** "Add .gitignore" (déjà présent)
   - **NE COCHEZ PAS** "Choose a license"
   - Cliquez sur "Create repository"

## Étape 2 : Créer un Personal Access Token

GitHub n'accepte plus les mots de passe pour les opérations Git.

1. **Allez sur** : https://github.com/settings/tokens
2. Cliquez sur **"Generate new token"** → **"Generate new token (classic)"**
3. **Note** : Donnez un nom (ex: "Apps Sync")
4. **Expiration** : Choisissez une durée (90 jours recommandé)
5. **Permissions** : Cochez **"repo"** (accès complet aux dépôts)
6. Cliquez sur **"Generate token"**
7. **COPIEZ LE TOKEN** (vous ne le reverrez plus !)
   - Exemple : `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Étape 3 : Push vers GitHub

Une fois le dépôt créé et le token obtenu, exécutez :

```powershell
cd c:\Apps
.\push-github-final.ps1
```

**Lorsque Git demande les identifiants :**
- **Username** : `ameni.compta@novaprint.tn`
- **Password** : Collez le **Personal Access Token** (pas le mot de passe !)

## Alternative : Push Direct

Si vous préférez faire le push directement :

```powershell
cd c:\Apps
$gitPath = "C:\Program Files\Git\bin\git.exe"
& $gitPath push -u origin main
```

**Identifiants :**
- Username : `ameni.compta@novaprint.tn`
- Password : Votre **Personal Access Token**

---

## Vérification

Après le push, vérifiez sur GitHub :
- https://github.com/ameni-compta/Apps

Tous vos fichiers devraient être présents.

---

**Rappel** : La synchronisation est NON DESTRUCTIVE.
- Aucun fichier ne sera supprimé
- Aucun --force ne sera utilisé
- Tous les fichiers sont préservés
