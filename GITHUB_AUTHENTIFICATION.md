# Authentification GitHub pour le push

GitHub **n'accepte plus le mot de passe du compte** pour les commandes Git (HTTPS). Il faut utiliser un **Personal Access Token (PAT)**.

## 1. Créer un Personal Access Token (PAT)

1. Allez sur **https://github.com/settings/tokens**
2. Cliquez sur **"Generate new token"** → **"Generate new token (classic)"**
3. Donnez un nom (ex. : `Apps-backup`) et cochez au minimum la permission **`repo`**
4. Cliquez sur **"Generate token"**
5. **Copiez le token** (il ne sera plus affiché ensuite)

## 2. Pousser le projet vers GitHub

Dans un terminal, à la racine du projet (x:\) :

```powershell
cd x:\
git push -u origin main
```

Quand Git demande :
- **Username** : `Ameni-Novaprint-R` (ou votre identifiant GitHub)
- **Password** : **collez le PAT** (pas le mot de passe du compte)

## 3. (Optionnel) Enregistrer le token pour ne pas le ressaisir

Sous Windows, Git Credential Manager peut mémoriser le token. À la première demande, entrez le PAT ; il sera réutilisé pour les prochains `git push`.

---

**Dépôt distant actuel :** `https://github.com/Ameni-Novaprint-R/Apps.git`  
**Branche :** `main`

**Si "Repository not found"** : le dépôt n’existe pas encore sur GitHub. Suivez les étapes dans **GITHUB_PREMIER_PUSH.md** pour créer le dépôt puis pousser.
