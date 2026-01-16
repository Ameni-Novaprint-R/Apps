# 📋 Guide d'Import du Planning de Maintenance Préventive

## ✅ Étape 1 : Vérifier que tout est prêt

La table `WEB_GMAO_PREVENTIVE` a été créée et étendue avec succès avec toutes les colonnes nécessaires.

## 📊 Étape 2 : Préparer votre fichier Excel

Votre fichier Excel doit contenir les colonnes suivantes (les noms peuvent varier, le script les détecte automatiquement) :

- **Tâche** : Description de la tâche de maintenance
- **Périodicité** : Fréquence (Quotidienne, Hebdomadaire, Mensuelle, Trimestrielle, Semestrielle, Annuelle)
- **Durée** : Temps estimé (ex: 5 min, 10 min, 1h, 2h)
- **Temps nécessaire** ou **Rôle** : Rôle requis (Opérateur, Technicien, Mécanicien, Électricien)
- **Spécifications / Observations** : Notes et observations
- **Référence** (optionnel) : Référence de la tâche (ex: K1, KBA 75)

## 🚀 Étape 3 : Importer les données

### Méthode 1 : Via la ligne de commande

```bash
python import_preventive_excel.py <chemin_vers_votre_fichier.xlsx> "KBA 75"
```

**Exemple :**
```bash
python import_preventive_excel.py "C:\Users\VotreNom\Documents\planning_kba75.xlsx" "KBA 75"
```

### Méthode 2 : Modifier le script directement

Si vous préférez, vous pouvez modifier le script `import_preventive_excel.py` pour mettre le chemin du fichier directement :

```python
if __name__ == "__main__":
    excel_file = "chemin/vers/votre/fichier.xlsx"  # Mettez votre chemin ici
    machine = "KBA 75"
    import_preventive_from_excel(excel_file, machine)
```

## 🔍 Étape 4 : Vérifier l'import

Après l'import, exécutez le script de test :

```bash
python test_preventive_display.py
```

Ce script vous indiquera :
- ✅ Si la table existe correctement
- 📊 Le nombre de tâches importées
- 📋 Un aperçu des données
- 📈 Un résumé par périodicité

## 🌐 Étape 5 : Tester l'affichage dans le navigateur

1. **Démarrer le serveur Flask** (si ce n'est pas déjà fait) :
   ```bash
   python app.py
   ```

2. **Ouvrir votre navigateur** et accéder à :
   ```
   http://localhost:5000/projet16/
   ```

3. **Cliquer sur "🔧 Maintenance Préventive"**

4. **Le tableau devrait s'afficher** avec :
   - Toutes les tâches groupées par périodicité
   - Un filtre par machine en haut
   - Les colonnes : Référence, Tâche, Périodicité, Durée, Rôle Requis, Personne en Charge, Spécifications/Observations

## ⚠️ Dépannage

### Erreur : "ModuleNotFoundError: No module named 'pandas'"

Installez pandas :
```bash
pip install pandas openpyxl
```

### Erreur : "Le fichier n'existe pas"

Vérifiez que le chemin vers votre fichier Excel est correct. Utilisez des guillemets si le chemin contient des espaces.

### Erreur lors de l'import

Le script affiche les colonnes trouvées dans votre fichier Excel. Vérifiez que les noms de colonnes correspondent approximativement à ceux attendus (le script fait une correspondance flexible).

### Aucune donnée ne s'affiche dans le navigateur

1. Vérifiez la console du navigateur (F12) pour voir les erreurs JavaScript
2. Vérifiez que le serveur Flask fonctionne
3. Vérifiez que les données sont bien dans la base avec `test_preventive_display.py`

## 📝 Notes importantes

- Le script détecte automatiquement les colonnes de votre fichier Excel
- Les données de `GP_POSTES` et `personel` restent en lecture seule
- Les modifications dans ces tables seront automatiquement synchronisées
- Vous pouvez filtrer par machine dans l'interface web

## 🎯 Prochaines étapes

Une fois l'import réussi et l'affichage vérifié, nous pourrons ajouter :
- Formulaire de création/édition de tâches
- Suivi d'exécution (marquer comme fait)
- Alertes pour les tâches à venir
- Export PDF/Excel
- Historique et statistiques

















