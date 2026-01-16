# 📋 Table WEB_GMAO_PREVENTIVE

## 🎯 Objectif

Créer une table dédiée aux interventions préventives dans le système GMAO, avec synchronisation automatique des données depuis les tables sources `GP_POSTES` et `personel`.

## 🗄️ Structure de la Table

| Colonne | Type | Description | Contraintes |
|---------|------|-------------|-------------|
| `ID` | INT IDENTITY | Identifiant unique | PRIMARY KEY, AUTO_INCREMENT |
| `Nom_GP_POSTES` | VARCHAR(50) | Nom de la machine sur laquelle l'intervention préventive a été réalisée | NULL, Lecture seule depuis la page |
| `NomPrenom_personel` | NVARCHAR(101) | Nom complet de l'opérateur (Nom + Prénom) | NULL, Synchronisé automatiquement |
| `Matricule_personel` | INT | Matricule de l'opérateur | NULL, FK → personel.Matricule |
| `DateCreation` | DATETIME | Date de création | DEFAULT GETDATE() |
| `DateModification` | DATETIME | Date de modification | DEFAULT GETDATE() |

## 🔗 Relations

- `Matricule_personel` → `personel.Matricule` (Foreign Key)

## 📌 Règles Fonctionnelles

### 1. **Nom_GP_POSTES**
- Doit être un choix issu de la colonne `Nom` de la table `GP_POSTES`
- Les données sont en **mode lecture seule** depuis la page : aucune modification ne doit impacter la table source `GP_POSTES`
- **Toute mise à jour dans `GP_POSTES`** sera automatiquement reflétée dans `WEB_GMAO_PREVENTIVE` via le trigger `TR_GP_POSTES_UPDATE_WEB_GMAO_PREVENTIVE`

### 2. **NomPrenom_personel**
- Contient le nom complet de l'opérateur (copie des colonnes `Nom` et `Prenom` de la table `personel`)
- Basé sur le `Matricule_personel` sélectionné
- Les données provenant de la table `personel` sont en **mode lecture seule** : aucune modification depuis la page ne doit affecter cette table `personel`
- **Toute mise à jour dans `personel`** sera automatiquement reflétée dans `WEB_GMAO_PREVENTIVE` via le trigger `TR_PERSONEL_UPDATE_WEB_GMAO_PREVENTIVE`

### 3. **Matricule_personel**
- Matricule de l'opérateur, copie de la colonne `Matricule` de la table `personel`
- Basé sur le nom/prénom sélectionné
- Contrainte de clé étrangère vers `personel.Matricule`

## 🔄 Triggers de Synchronisation

### TR_GP_POSTES_UPDATE_WEB_GMAO_PREVENTIVE
- **Déclencheur** : Après mise à jour dans `GP_POSTES`
- **Action** : Met à jour automatiquement `Nom_GP_POSTES` dans `WEB_GMAO_PREVENTIVE` si le nom du poste a changé

### TR_PERSONEL_UPDATE_WEB_GMAO_PREVENTIVE
- **Déclencheur** : Après mise à jour dans `personel`
- **Action** : Met à jour automatiquement `NomPrenom_personel` dans `WEB_GMAO_PREVENTIVE` si le nom ou prénom de l'opérateur a changé

### TR_WEB_GMAO_PREVENTIVE_INSERT
- **Déclencheur** : Après insertion dans `WEB_GMAO_PREVENTIVE`
- **Action** : Synchronise automatiquement `NomPrenom_personel` depuis `personel` lors de l'insertion d'une nouvelle ligne

### TR_WEB_GMAO_PREVENTIVE_UPDATE
- **Déclencheur** : Après mise à jour dans `WEB_GMAO_PREVENTIVE`
- **Action** : Synchronise automatiquement `NomPrenom_personel` depuis `personel` si `Matricule_personel` a changé

## 📊 Index

- `IX_WEB_GMAO_PREVENTIVE_Matricule_personel` : Index sur `Matricule_personel` pour améliorer les performances des jointures
- `IX_WEB_GMAO_PREVENTIVE_Nom_GP_POSTES` : Index sur `Nom_GP_POSTES` pour améliorer les performances des recherches

## ⚠️ Important

1. **Lecture seule depuis la page** : Les données de `GP_POSTES` et `personel` ne doivent jamais être modifiées depuis l'interface web du projet 16
2. **Synchronisation automatique** : Toute modification dans `GP_POSTES` ou `personel` sera automatiquement reflétée dans `WEB_GMAO_PREVENTIVE` grâce aux triggers
3. **Intégrité référentielle** : La contrainte de clé étrangère garantit que `Matricule_personel` existe toujours dans `personel`

## 📝 Exemple d'utilisation

```sql
-- Insérer une intervention préventive
INSERT INTO WEB_GMAO_PREVENTIVE (Nom_GP_POSTES, Matricule_personel)
VALUES ('XL75', 12345);

-- Le trigger TR_WEB_GMAO_PREVENTIVE_INSERT synchronisera automatiquement NomPrenom_personel
-- depuis personel en fonction du Matricule_personel

-- Si le nom d'un opérateur change dans personel, le trigger TR_PERSONEL_UPDATE_WEB_GMAO_PREVENTIVE
-- mettra automatiquement à jour NomPrenom_personel dans toutes les lignes concernées
```

## 🔧 Scripts de Création

- **SQL** : `create_web_gmao_preventive.sql`
- **Python** : `setup_web_gmao_preventive.py`

Les deux scripts créent la table, les index et tous les triggers nécessaires.

















