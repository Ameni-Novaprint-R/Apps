# Projet 22 - Gestion des Employés et Mots de Passe

## 🎯 Objectif

Le Projet 22 permet de gérer les employés dans la table `personel` et de définir des mots de passe pour chaque employé. Les mots de passe sont hachés avec bcrypt pour garantir la sécurité.

## 🗄️ Structure de la Base de Données

### Table `personel`

| Colonne | Type | Description | Contraintes |
|---------|------|-------------|-------------|
| `Matricule` | INT | Identifiant unique de l'employé | PRIMARY KEY |
| `Nom` | NVARCHAR(50) | Nom de l'employé | NOT NULL |
| `Prenom` | NVARCHAR(50) | Prénom de l'employé | NOT NULL |
| `Adresse_mail` | NVARCHAR(50) | Adresse email | NULL |
| `mdp` | VARCHAR(60) | Mot de passe haché avec bcrypt | NULL |
| `archive` | TINYINT | Indicateur d'archivage (0 = actif, 1 = archivé) | NOT NULL DEFAULT 0 |

## 🔐 Sécurité des Mots de Passe

- Les mots de passe sont hachés avec **bcrypt**
- Le hash bcrypt produit une chaîne de 60 caractères
- Les mots de passe en clair ne sont jamais stockés dans la base de données
- Minimum 6 caractères requis pour un mot de passe

## 📋 Fonctionnalités

### 1. **Liste des Employés**
- Affichage de tous les employés
- Indication visuelle si un employé a un mot de passe ou non
- Indication si un employé est archivé
- Filtrage et tri automatiques

### 2. **Création d'Employé**
- Ajout d'un nouvel employé avec :
  - Matricule (obligatoire, unique)
  - Nom (obligatoire)
  - Prénom (obligatoire)
  - Email (optionnel)
  - Mot de passe (optionnel, peut être défini plus tard)

### 3. **Modification d'Employé**
- Mise à jour des informations :
  - Nom
  - Prénom
  - Email
- Le matricule ne peut pas être modifié
- Le mot de passe doit être modifié via la fonction dédiée

### 4. **Gestion des Mots de Passe**
- Définition d'un mot de passe pour un employé
- Modification d'un mot de passe existant
- Vérification de la force du mot de passe (minimum 6 caractères)

### 5. **Archivage**
- Archiver un employé (le rend inactif)
- Désarchiver un employé (le réactive)
- Les employés archivés sont affichés différemment dans l'interface

## 🚀 Utilisation

### Accès à l'interface

1. Accéder à la page via le menu : **👥 Employés**
2. URL directe : `/projet22/`

### Créer un employé

1. Cliquer sur **➕ Ajouter un employé**
2. Remplir le formulaire :
   - Matricule (obligatoire)
   - Nom (obligatoire)
   - Prénom (obligatoire)
   - Email (optionnel)
   - Mot de passe (optionnel, peut être défini plus tard)
3. Cliquer sur **Enregistrer**

### Définir un mot de passe

1. Cliquer sur **🔑 Mot de passe** sur la carte de l'employé
2. Entrer le nouveau mot de passe (minimum 6 caractères)
3. Cliquer sur **Enregistrer**

### Modifier un employé

1. Cliquer sur **✏️ Modifier** sur la carte de l'employé
2. Modifier les informations souhaitées
3. Cliquer sur **Enregistrer**

### Archiver/Désarchiver

1. Cliquer sur **📦 Archiver** pour archiver un employé
2. Cliquer sur **✅ Désarchiver** pour réactiver un employé archivé

## 🔧 API Endpoints

### GET `/projet22/api/employes`
Récupère la liste de tous les employés.

**Réponse :**
```json
{
  "success": true,
  "employes": [
    {
      "matricule": 123,
      "nom": "Dupont",
      "prenom": "Jean",
      "email": "jean.dupont@example.com",
      "a_mot_de_passe": true,
      "archive": false
    }
  ]
}
```

### GET `/projet22/api/employe/<matricule>`
Récupère un employé par son matricule.

### POST `/projet22/api/create`
Crée un nouvel employé.

**Corps de la requête :**
```json
{
  "matricule": 123,
  "nom": "Dupont",
  "prenom": "Jean",
  "email": "jean.dupont@example.com",
  "mdp": "motdepasse123"
}
```

### PUT `/projet22/api/update/<matricule>`
Met à jour un employé.

**Corps de la requête :**
```json
{
  "nom": "Dupont",
  "prenom": "Jean",
  "email": "jean.dupont@example.com"
}
```

### POST `/projet22/api/set-password/<matricule>`
Définit ou met à jour le mot de passe d'un employé.

**Corps de la requête :**
```json
{
  "mdp": "nouveaumotdepasse"
}
```

### POST `/projet22/api/archive/<matricule>`
Archive ou désarchive un employé.

**Corps de la requête :**
```json
{
  "archive": true
}
```

### POST `/projet22/api/verify-password`
Vérifie si un mot de passe est correct pour un employé.

**Corps de la requête :**
```json
{
  "matricule": 123,
  "mdp": "motdepasse"
}
```

**Réponse :**
```json
{
  "success": true,
  "valid": true
}
```

## 📦 Dépendances

- **bcrypt** : Pour le hachage des mots de passe
  ```bash
  pip install bcrypt
  ```

## 🔒 Sécurité

- Les mots de passe sont toujours hachés avant d'être stockés
- Les mots de passe en clair ne sont jamais stockés dans la base de données
- Utilisation de bcrypt avec salt automatique pour chaque mot de passe
- Validation de la longueur minimale des mots de passe (6 caractères)

## 📝 Notes

- Le matricule est l'identifiant unique et ne peut pas être modifié
- Un employé peut être créé sans mot de passe et le mot de passe peut être défini plus tard
- Les employés archivés sont toujours visibles mais marqués comme archivés
- L'archivage ne supprime pas l'employé, il le marque simplement comme inactif
