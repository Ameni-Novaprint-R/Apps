# Guide de récupération à partir de GitHub

## Dernière synchronisation
- **Commit** : 9791016 (Projet 23 - Situation Trésorerie)
- **Contenu** : app.py, logic/projet23.py, routes/projet23_routes.py, templates/projet23.html, migrations, droits accès, auth (super-user 1)

---

## Fichiers essentiels présents dans GitHub

### Application principale
| Fichier | Statut |
|---------|--------|
| app.py | ✓ |
| db.py | ✓ |
| wsgi.py | ✓ |
| requirements.txt | ✓ |

### Logic (23 projets + auth)
| Module | Statut |
|--------|--------|
| logic/auth.py | ✓ |
| logic/project_routes.py | ✓ |
| logic/rapport_cq.py | ✓ |
| logic/projet1 à projet23 | ✓ |
| logic/crystal_reports_logic.py | ✓ |

### Routes
| Fichier | Statut |
|---------|--------|
| routes/auth_routes.py | ✓ |
| routes/admin_routes.py | ✓ |
| routes/projet11 à projet23_routes | ✓ |
| routes/crystal_reports_routes.py | ✓ |
| routes/renommer_table_route.py | ✓ |

### Templates (52 fichiers)
- base.html, index.html, projet1 à projet23.html | ✓
- Tous les templates des 23 projets | ✓

### Static
- style.css, projet10.css | ✓
- logo-novaprint.png | ✓
- js/html2pdf.bundle.min.js | ✓

### Scripts de migration/projet 23
- creer_table_web_projet23_synthese.py | ✓
- inserer_droits_projet23_matricules.py | ✓

---

## Procédure de récupération complète

1. **Cloner le dépôt**
   ```
   git clone https://github.com/Ameni-Novaprint-R/Apps.git
   cd Apps
   ```

2. **Installer les dépendances**
   ```
   pip install -r requirements.txt
   ```

3. **Configurer la base de données**
   - Vérifier/modifier `db.py` (DB_CONFIG : serveur, base, identifiants)
   - Exécuter les migrations si nécessaire :
     - `python creer_table_web_projet23_synthese.py`
     - `python inserer_droits_projet23_matricules.py`

4. **Démarrer l'application**
   ```
   python app.py
   ```
   Ou via wsgi pour production.

---

## Fichiers non synchronisés (à vérifier)

| Fichier | Action recommandée |
|---------|--------------------|
| logic/projet10.py | Modifié localement – à valider et committer si correct |
| templates/projet10.html | Modifié localement – à valider et committer si correct |
| sync_results/*.json | Générés automatiquement – optionnel |
| projet23/donnees_a_analyser/*.pdf | Données PDF – ne pas versionner (fichiers volumineux) |

---

## Points critiques

- **Base de données** : Non incluse dans Git (config dans db.py uniquement). Sauvegarder séparément.
- **Données projet 23** : Les PDF XRT sont dans `projet23/donnees_a_analyser/` – recréer ou restaurer manuellement.
- **Config sensible** : .env, config.ini sont dans .gitignore – à configurer sur chaque environnement.
