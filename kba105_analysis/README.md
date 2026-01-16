# Analyse de la Documentation KBA105

## 📋 Description

Ce script analyse l'archive `kba105.zip` contenant la documentation de la machine KBA105 pour extraire toutes les tâches de maintenance préventive.

## 📁 Structure

```
kba105_analysis/
├── kba105.zip                    # Archive à placer ici (à télécharger)
├── analyze_kba105.py             # Script d'analyse principal
├── kba105_maintenance_preventive.xlsx  # Fichier Excel généré (après exécution)
└── README.md                     # Ce fichier
```

## 🚀 Utilisation

### 1. Préparation

1. Placez le fichier `kba105.zip` dans le dossier `C:\Apps\kba105_analysis\`
2. Assurez-vous que Python 3.x est installé
3. Installez les dépendances nécessaires :

```bash
pip install openpyxl
```

### 2. Exécution

```bash
cd C:\Apps\kba105_analysis
python analyze_kba105.py
```

### 3. Résultat

Le script génère un fichier Excel `kba105_maintenance_preventive.xlsx` avec :

- **Onglet 1 : Tâches Maintenance Préventive KBA105**
  - N° | Libellé de la tâche | Périodicité | Type de document | Nom du fichier source | Composant concerné

- **Onglet 2 : Calendrier Prévision 2026**
  - Date | Jour | Semaine | Jour férié | Tâches prévues
  - Inclut les jours fériés tunisiens (du projet18)
  - Affiche les tâches prévues pour chaque date selon leur périodicité

## 🔍 Fonctionnalités

### Identification des tâches

Le script identifie automatiquement les tâches de maintenance préventive en analysant les noms de fichiers pour détecter :

- **Mots-clés de maintenance préventive** : wartung, maintenance, prüfung, vérification, inspektion, inspection, etc.
- **Exclusion de la maintenance corrective** : réparation, panne, défaut, etc.

### Extraction des informations

1. **Libellé de la tâche** : Traduit automatiquement de l'allemand vers le français
2. **Périodicité** : Détectée depuis les patterns dans le nom de fichier
   - Quotidienne (täglich, daily, jour)
   - Hebdomadaire (wöchentlich, weekly, semaine)
   - Mensuelle (monatlich, monthly, mois)
   - Trimestrielle (vierteljährlich, quarterly, trimestre)
   - Annuelle (jährlich, yearly, année)
3. **Composant concerné** : Identifié depuis les patterns techniques (walze, motor, pumpe, etc.)
4. **Type de document** : Manuel, Plan, Procédure, Liste, Guide, etc.

### Calendrier de prévision

- Génère un calendrier complet pour l'année 2026
- Inclut tous les jours fériés tunisiens (du projet18)
- Calcule automatiquement les dates d'exécution selon la périodicité
- Met en évidence les jours fériés en rouge
- Affiche les tâches prévues pour chaque date

## 📊 Format de sortie Excel

### Colonnes principales

| Colonne | Description |
|---------|-------------|
| N° | Numéro séquentiel de la tâche |
| Libellé de la tâche | Description traduite en français |
| Périodicité | Quotidienne / Hebdomadaire / Mensuelle / Trimestrielle / Annuelle |
| Type de document | Manuel / Plan / Procédure / Liste / Guide / etc. |
| Nom du fichier source | Nom original du fichier dans l'archive |
| Composant concerné | Composant de la machine concerné |

### Calendrier

| Colonne | Description |
|---------|-------------|
| Date | Date au format JJ/MM/AAAA |
| Jour | Jour de la semaine |
| Semaine | Numéro de semaine ISO |
| Jour férié | Nom du jour férié (si applicable) |
| Tâches prévues | Liste des tâches à exécuter ce jour |

## 🎯 Jours fériés tunisiens inclus

Les jours fériés tunisiens pour 2026 sont automatiquement inclus (depuis le projet18) :

**Jours fériés fixes :**
- 1er janvier : Jour de l'An
- 20 mars : Fête de l'Indépendance
- 9 avril : Journée des Martyrs
- 1er mai : Fête du Travail
- 25 juillet : Fête de la République
- 13 août : Fête de la Femme
- 15 octobre : Fête de l'Évacuation
- 17 décembre : Fête de la Révolution

**Jours fériés religieux :**
- 21-22 mars : Aïd al-Fitr
- 26-27 mai : Aïd al-Adha
- 15 juin : Nouvel An hégirien
- 24 août : Mouled

## ⚙️ Personnalisation

### Modifier les patterns de détection

Éditez le fichier `analyze_kba105.py` pour ajuster :

- `TRANSLATIONS` : Dictionnaire de traduction allemand → français
- `PERIODICITY_PATTERNS` : Patterns pour identifier la périodicité
- `COMPONENT_PATTERNS` : Patterns pour identifier les composants
- `DOCUMENT_TYPES` : Patterns pour identifier les types de documents

### Changer l'année du calendrier

Modifiez la fonction `generate_calendar_with_holidays()` pour changer l'année.

## 📝 Notes importantes

- Le script analyse uniquement les **noms de fichiers**, pas le contenu des fichiers
- Les traductions sont automatiques et peuvent nécessiter des ajustements manuels
- Les jours fériés religieux sont basés sur des dates prévisionnelles (calendrier lunaire)
- Le script ne modifie pas l'archive originale, seulement la lit

## 🐛 Dépannage

### Erreur : "Le fichier kba105.zip n'existe pas"

Vérifiez que le fichier `kba105.zip` est bien placé dans le dossier `C:\Apps\kba105_analysis\`

### Erreur : "ModuleNotFoundError: No module named 'openpyxl'"

Installez la dépendance :
```bash
pip install openpyxl
```

### Aucune tâche trouvée

Vérifiez que l'archive contient bien des fichiers de documentation avec des noms contenant des mots-clés de maintenance préventive.

## 📞 Support

Pour toute question ou problème, consultez les logs d'exécution du script.

