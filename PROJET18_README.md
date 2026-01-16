# 📅 Projet 18 - Agenda Semainier 2026 (Tunisie)

## 📄 Description

Le **Projet 18** est une application Flask permettant de générer un agenda semainier pour l'année 2026, spécialement conçu pour la Tunisie. Il génère des PDFs au format Quo Vadis avec support multilingue (Français, Anglais, Arabe) et inclut les jours fériés tunisiens.

---

## 🎯 Objectifs

1. **Générer un agenda semainier 2026** complet avec toutes les semaines de l'année
2. **Format Quo Vadis** : 2 pages par semaine (Lundi-Mercredi / Jeudi-Dimanche)
3. **Support multilingue** : Français, Anglais, Arabe avec affichage correct du texte arabe
4. **Jours fériés tunisiens** : Marqués automatiquement en rouge
5. **Export PDF** : Génération de PDFs optimisés pour l'impression

---

## 🗄️ Structure de la Base de Données

Le Projet 18 n'utilise pas de base de données. Toutes les données (semaines, jours fériés) sont générées dynamiquement en Python.

### Jours fériés en Tunisie pour 2026

- **Jours fériés fixes** : Jour de l'an, Fête de la Révolution, Fête de l'Indépendance, Jour des Martyrs, Fête du Travail, Fête de la République, Fête de la Femme, Jour de l'Évacuation
- **Jours fériés religieux** : Aïd al-Fitr, Aïd al-Adha, Mouled, Ras el-Am (approximatifs selon le calendrier lunaire)

---

## 📁 Structure des Fichiers

### Backend

- **`logic/projet18.py`** : Logique métier
  - `get_semaines_2026()` : Génère les 52 semaines de 2026
  - `is_jour_ferie(date)` : Vérifie si une date est un jour férié
  - `get_nom_jour_ferie(date)` : Retourne le nom du jour férié
  - `get_mois_nom(mois_numero)` : Retourne le nom du mois en français

- **`routes/projet18_routes.py`** : Routes Flask
  - `/projet18/` : Page principale avec aperçu
  - `/projet18/export-pdf` : Export PDF standard (Français uniquement)
  - `/projet18/export-pdf-multilang` : Export PDF multilingue (FR/EN/AR)

### Frontend

- **`templates/projet18.html`** : Template principal
  - Aperçu des premières semaines
  - Boutons d'export PDF
  - Informations sur l'agenda

---

## 🚀 Fonctionnalités

### 1. Génération des Semaines

- ✅ **52 semaines complètes** de 2026
- ✅ Chaque semaine commence le **lundi** et se termine le **dimanche**
- ✅ La première semaine commence le **29 décembre 2025** (pour inclure le 1er janvier 2026)
- ✅ Dates exactes pour chaque jour de la semaine

### 2. Export PDF Standard

- 📄 Format A4 portrait
- 📅 Une semaine par page
- 🇫🇷 Texte en français uniquement
- 🔴 Jours fériés marqués en rouge
- 📝 Espaces pour notes et rendez-vous

### 3. Export PDF Multilingue

- 📄 Format A4 portrait
- 📅 **2 pages par semaine** (format Quo Vadis)
  - Page 1 : Lundi, Mardi, Mercredi
  - Page 2 : Jeudi, Vendredi, Samedi, Dimanche
- 🌍 **3 langues** : Français, Anglais, Arabe
- ✅ **Texte arabe correctement affiché** avec lettres attachées et ordre RTL
- 🔴 Jours fériés marqués en rouge
- 📊 Mini-calendrier mensuel sur chaque page
- 📝 Zone de notes sur chaque page
- ⏰ Grille horaire de 8h à 20h

### 4. Jours Fériés

- ✅ Détection automatique des jours fériés tunisiens
- 🔴 Affichage en rouge dans le PDF
- 📝 Nom du jour férié affiché sous la date
- 📅 Jours fériés fixes et religieux inclus

---

## 🎨 Technologies Utilisées

### Backend
- **Flask** : Framework web Python
- **ReportLab** : Génération de PDFs
- **arabic-reshaper** : Formes contextuelles pour le texte arabe
- **python-bidi** : Support bidirectionnel pour l'arabe

### Frontend
- **HTML5** / **CSS3** : Structure et style
- **Jinja2** : Templates Flask

### Polices
- **Arial Unicode MS** : Support complet de l'arabe (si disponible)
- **Tahoma** : Alternative pour l'arabe
- **DejaVuSans** : Fallback si les autres ne sont pas disponibles
- **Helvetica** : Par défaut (ne supporte pas l'arabe)

---

## 💡 Utilisation

### Page principale

1. Accédez à http://localhost:5000/projet18/
2. Consultez l'aperçu des premières semaines
3. Choisissez le type d'export :
   - **📄 Télécharger en PDF** : Version standard (français)
   - **🌍 Version Multilingue (AR/EN)** : Version avec 3 langues

### Export PDF Standard

1. Cliquez sur **"📄 Télécharger en PDF"**
2. Le PDF est généré avec toutes les semaines de 2026
3. Chaque semaine occupe une page complète
4. Les jours fériés sont marqués en rouge

### Export PDF Multilingue

1. Cliquez sur **"🌍 Version Multilingue (AR/EN)"**
2. Le PDF est généré avec le format Quo Vadis (2 pages par semaine)
3. Chaque jour affiche :
   - Date en haut (grande, bleue)
   - Nom du jour en 3 langues : Français / Anglais / Arabe
4. Le texte arabe est correctement affiché avec les lettres attachées
5. Mini-calendrier mensuel sur chaque page
6. Grille horaire de 8h à 20h pour chaque jour

---

## 🔧 Installation des Dépendances

```bash
pip install flask reportlab arabic-reshaper python-bidi
```

### Dépendances requises

- **Flask** : Framework web
- **ReportLab** : Génération de PDFs
- **arabic-reshaper** : Pour les formes contextuelles arabes
- **python-bidi** : Pour le support bidirectionnel

---

## 📊 Format du PDF Multilingue

### Structure d'une semaine

#### Page 1 : Lundi, Mardi, Mercredi

```
┌─────────────────────────────────────────────────┐
│ Semaine Week 01 الأسبوع                         │
├──────────────┬──────────────┬──────────────────┤
│     01       │     02       │       03         │
│ Lundi /      │ Mardi /      │ Mercredi /       │
│ Monday /     │ Tuesday /    │ Wednesday /      │
│ الإثنين      │ الثلاثاء      │ الأربعاء         │
│              │              │                  │
│ 8h  ──────── │ 8h  ──────── │ 8h  ────────    │
│ 9h  ──────── │ 9h  ──────── │ 9h  ────────    │
│ ...          │ ...          │ ...             │
│ 20h ──────── │ 20h ──────── │ 20h ────────    │
│              │              │                  │
│ Notes:       │ Notes:       │ Notes:          │
│ ──────────── │ ──────────── │ ─────────────── │
└──────────────┴──────────────┴──────────────────┘
```

#### Page 2 : Jeudi, Vendredi, Samedi, Dimanche

Même structure avec 4 colonnes pour les 4 jours restants.

---

## 🌐 Accès à l'Interface Web

### Pages principales

- **Page d'accueil** : http://localhost:5000/projet18/
- **Export PDF standard** : http://localhost:5000/projet18/export-pdf
- **Export PDF multilingue** : http://localhost:5000/projet18/export-pdf-multilang

### Navigation

Le Projet 18 est accessible depuis :
- 🏠 Page d'accueil : "📅 Projet 18 – Agenda Semainier 2026"

---

## 🔤 Support du Texte Arabe

### Correction de l'affichage

Le Projet 18 utilise une fonction spéciale `fix_arabic_text()` pour corriger l'affichage du texte arabe :

1. **Reshape** : Utilise `arabic-reshaper` pour obtenir les bonnes formes contextuelles (lettres attachées)
2. **Inversion** : Inverse l'ordre des caractères pour l'affichage visuel RTL (car ReportLab affiche de gauche à droite)
3. **Police** : Utilise une police qui supporte l'arabe (Arial Unicode MS, Tahoma, ou DejaVuSans)

### Résultat

- ✅ Texte arabe lisible avec les lettres attachées
- ✅ Ordre correct (de droite à gauche)
- ✅ Pas de carrés ou caractères bizarres
- ✅ Support complet de l'arabe dans les PDFs

---

## 📝 Exemples de Jours Fériés

| Date | Nom du jour férié |
|------|-------------------|
| 1er janvier | Nouvel An |
| 20 mars | Fête de l'Indépendance |
| 1er mai | Fête du Travail |
| 25 juillet | Fête de la République |
| 13 août | Fête de la Femme |
| 15 octobre | Jour de l'Évacuation |

---

## 🛠️ Maintenance

### Mise à jour des jours fériés

Les jours fériés sont définis dans `logic/projet18.py` dans la liste `JOURS_FERIES_TUNISIE_2026`.

Pour ajouter ou modifier un jour férié :
1. Ouvrez `logic/projet18.py`
2. Modifiez la liste `JOURS_FERIES_TUNISIE_2026`
3. Ajoutez le nom dans le dictionnaire `jours_feries_noms` de la fonction `get_nom_jour_ferie()`

### Changement d'année

Pour générer un agenda pour une autre année :
1. Modifiez la fonction `get_semaines_2026()` dans `logic/projet18.py`
2. Changez l'année de référence
3. Mettez à jour la liste des jours fériés

---

## 🔐 Sécurité

- ✅ Validation des dates
- ✅ Gestion des erreurs avec messages appropriés
- ✅ Protection contre les erreurs de génération PDF

---

## 📈 Améliorations Futures Possibles

1. 🔍 **Filtres** :
   - Filtrer par mois
   - Filtrer par trimestre
   - Recherche de dates

2. 📥 **Export** :
   - Export Excel
   - Export CSV
   - Export iCal

3. 🎨 **Personnalisation** :
   - Couleurs personnalisables
   - Ajout de logos
   - Personnalisation des polices

4. 📱 **Responsive** :
   - Version mobile optimisée
   - Application progressive (PWA)

5. 🌍 **Autres pays** :
   - Support pour d'autres pays
   - Jours fériés configurables

---

## 🐛 Dépannage

### Le texte arabe s'affiche mal

1. Vérifiez que `arabic-reshaper` et `python-bidi` sont installés :
   ```bash
   pip install arabic-reshaper python-bidi
   ```

2. Vérifiez qu'une police arabe est disponible :
   - Arial Unicode MS (Windows)
   - Tahoma (Windows)
   - DejaVuSans (Linux)

### Le PDF ne se génère pas

1. Vérifiez que ReportLab est installé :
   ```bash
   pip install reportlab
   ```

2. Vérifiez les logs dans la console Flask

### Les jours fériés ne s'affichent pas

1. Vérifiez que les dates dans `JOURS_FERIES_TUNISIE_2026` sont correctes
2. Vérifiez que les noms sont définis dans `get_nom_jour_ferie()`

---

## 📞 Support

Pour toute question ou problème, contactez l'équipe de développement.

---

## 📚 Références

- **Format Quo Vadis** : Format d'agenda populaire avec 2 pages par semaine
- **ReportLab** : https://www.reportlab.com/
- **arabic-reshaper** : https://github.com/mpcabd/python-arabic-reshaper
- **python-bidi** : https://github.com/MeirKriheli/python-bidi

---

**Date de création** : Décembre 2025  
**Version** : 1.0  
**Statut** : ✅ Opérationnel

---

## ✅ Projet Terminé !

Le Projet 18 est maintenant **opérationnel** et prêt à générer des agendas semainiers 2026 pour la Tunisie ! 🎉

**Bon agenda ! 📅📆**











