# Créer le dépôt GitHub puis pousser

Le token fonctionne, mais le dépôt **Apps** n'existe pas encore sur GitHub.

## 1. Créer le dépôt sur GitHub (2 minutes)

1. Ouvrez : **https://github.com/new**
2. Connectez-vous si besoin (compte lié au token).
3. **Repository name** : `Apps` (exactement)
4. **Description** (optionnel) : "Application web 22 projets"
5. Choisissez **Private** ou **Public**
6. **Ne cochez pas** "Add a README file" ni ".gitignore"
7. Cliquez sur **Create repository**

## 2. Pousser le code

Une fois le dépôt créé, dans **PowerShell** à la racine du projet :

```powershell
cd x:\
git push -u origin main
```

Quand Git demande le mot de passe : **collez votre token** (celui que vous avez créé).

Ou en une seule commande (remplacez VOTRE_TOKEN par le token) :

```powershell
git push https://Ameni-Novaprint-R:VOTRE_TOKEN@github.com/Ameni-Novaprint-R/Apps.git main
git branch --set-upstream-to=origin main
```

---

**Sécurité** : vous avez partagé le token dans le chat. Après le premier push réussi, il est recommandé de le **révoquer** sur https://github.com/settings/tokens et d’en créer un **nouveau** pour les prochains push (à ne plus partager).
