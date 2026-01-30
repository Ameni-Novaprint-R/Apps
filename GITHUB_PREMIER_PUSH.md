# Premier push vers GitHub – Application web 22 projets

## État actuel

- **Git** est initialisé à la racine du projet (x:\)
- **Premier commit** créé : 196 fichiers (app Flask, routes, logic, templates, scripts)
- **Remote** configuré : `origin` → `https://github.com/ameni-compta/Apps.git`
- Le dépôt distant **n’existe pas encore** ou n’est pas accessible → il faut le créer puis pousser.

## Étapes à suivre

### 1. Créer le dépôt sur GitHub

1. Allez sur **https://github.com/new**
2. Connectez-vous avec le compte **ameni-compta** (email : ameni.comptanova@gmail.com)
3. **Repository name** : `Apps` (ou un autre nom si vous préférez)
4. **Visibility** : Private ou Public
5. **Ne cochez pas** "Add a README" ni ".gitignore" (le projet en a déjà)
6. Cliquez sur **Create repository**

### 2. Créer un Personal Access Token (PAT)

GitHub n’accepte plus le mot de passe du compte pour Git. Il faut un **token** :

1. Allez sur **https://github.com/settings/tokens**
2. **Generate new token** → **Generate new token (classic)**
3. Nom : par ex. `Apps-backup`
4. Cochez **repo** (accès aux dépôts)
5. **Generate token** puis **copiez le token** (il ne s’affichera plus)

### 3. Pousser le code depuis votre PC

Ouvrez **PowerShell** ou **Invite de commandes** :

```powershell
cd x:\
git push -u origin main
```

Quand Git demande :
- **Username** : `ameni-compta`
- **Password** : **collez le PAT** (pas le mot de passe du compte)

Si le dépôt a un autre nom que `Apps`, mettez à jour l’URL :

```powershell
git remote set-url origin https://github.com/ameni-compta/VOTRE_NOM_REPO.git
git push -u origin main
```

---

## Contenu sauvegardé dans ce commit

- **app.py**, **db.py**, **wsgi.py**
- **logic/** (projet1 à projet22, auth, etc.)
- **routes/** (projet11 à projet22, admin, auth, crystal_reports, etc.)
- **templates/** (tous les HTML)
- **static/**, **sql/**, **crystalreport/** (fichiers .rpt)
- **requirements.txt**
- Scripts .py, .bat, .ps1, .sql et documentation .md

Les dossiers **Integr11**, **kba105_analysis**, **projet17**, **PrintToB_Utilisation** sont exclus du dépôt (très volumineux). Pour les inclure plus tard, retirez-les du fichier `.gitignore` à la racine.

---

## Adresse du dépôt après le push

Une fois le push réussi, le projet sera disponible à :

**https://github.com/ameni-compta/Apps**  
(ou l’URL correspondant au nom du dépôt que vous avez créé)

Vous pourrez ainsi restaurer un fichier ou tout le projet en cas de suppression ou d’erreur.
