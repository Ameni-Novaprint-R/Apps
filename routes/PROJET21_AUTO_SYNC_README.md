# Synchronisation Automatique Projet 21

## Vue d'ensemble

Le système de synchronisation automatique exécute une synchronisation complète de la base de données chaque jour à **05:00 AM** et effectue une vérification automatique des résultats.

## Configuration requise

### 1. Installation des dépendances

```bash
pip install apscheduler
```

### 2. Configuration de l'email

Le système nécessite une configuration SMTP pour envoyer les notifications. Deux options :

#### Option A : Variables d'environnement (recommandé)

Définir la variable d'environnement `SMTP_PASSWORD` avec le mot de passe de l'email `ameni.compta@novaprint.tn`.

#### Option B : Modification du code

Modifier le fichier `routes/projet21_auto_sync.py` et mettre à jour :

```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',  # Adapter selon votre serveur SMTP
    'smtp_port': 587,
    'sender_email': 'ameni.compta@novaprint.tn',
    'sender_password': 'VOTRE_MOT_DE_PASSE',  # ⚠️ À configurer
    'recipient_email': 'ameni.compta@novaprint.tn'
}
```

**Note importante** : Si vous utilisez Gmail, vous devrez peut-être créer un "Mot de passe d'application" plutôt qu'utiliser votre mot de passe principal.

## Fonctionnement

### Synchronisation automatique

- **Horaire** : Chaque jour à 05:00 AM
- **Processus** :
  1. Exécution de la synchronisation complète
  2. Vérification automatique des résultats
  3. Sauvegarde du résultat JSON uniquement s'il y a des problèmes (hors GS_INVENTAIRES)
  4. Envoi d'email si :
     - La synchronisation échoue
     - Des problèmes sont détectés lors de la vérification

### Stockage des résultats

- **Dossier** : `sync_results/`
- **Fichier** : `last_auto_sync_result.json` (écrasé à chaque nouvelle synchronisation)
- **Conservation** : Seulement le dernier résultat (24h max)
- **Contenu** : Résultats complets de vérification uniquement si problèmes détectés

### Notifications email

Les emails sont envoyés dans les cas suivants :

1. **Échec de synchronisation** : Email immédiat avec détails de l'erreur
2. **Problèmes détectés** : Email avec résumé des problèmes (hors GS_INVENTAIRES qui est acceptable)

## Interface utilisateur

### Section "Synchronisation Automatique"

- **Activation/Désactivation** : Case à cocher pour activer/désactiver la synchronisation automatique
- **Statut** : Affiche si la synchronisation est activée ou désactivée

### Section "Vérification Synchronisation Automatique"

Affiche le dernier résultat de vérification automatique avec :

- **Timestamp** : Date et heure de la dernière exécution
- **Résumé** : Identique à la vérification manuelle
- **Détails** : Toutes les sections détaillées (lignes manquantes, lignes supplémentaires, doublons de PK)

**Note** : Si aucun problème n'a été détecté (hors GS_INVENTAIRES), aucun résultat n'est affiché car il n'a pas été sauvegardé.

## Fichiers créés/modifiés

### Nouveaux fichiers

- `routes/projet21_auto_sync.py` : Module principal de synchronisation automatique
- `sync_results/` : Dossier pour stocker les résultats JSON
- `sync_results/last_auto_sync_result.json` : Dernier résultat (si problèmes détectés)
- `sync_results/auto_sync_config.json` : Configuration (état activé/désactivé)

### Fichiers modifiés

- `app.py` : Intégration du scheduler APScheduler
- `routes/projet21_routes.py` : Routes API pour gérer la synchronisation automatique
- `templates/projet21/index.html` : Interface utilisateur pour la synchronisation automatique

## Dépannage

### Le scheduler ne démarre pas

1. Vérifier que APScheduler est installé : `pip install apscheduler`
2. Vérifier les logs au démarrage de Flask pour voir les messages d'erreur

### Les emails ne sont pas envoyés

1. Vérifier la configuration SMTP dans `projet21_auto_sync.py`
2. Vérifier que le mot de passe est correct (ou variable d'environnement `SMTP_PASSWORD`)
3. Vérifier les logs pour voir les erreurs d'envoi d'email

### La synchronisation automatique ne s'exécute pas

1. Vérifier que la synchronisation automatique est activée dans l'interface
2. Vérifier que le serveur Flask est toujours démarré
3. Vérifier les logs pour voir si le scheduler est actif

## Sécurité

- ⚠️ **Ne jamais commiter le mot de passe SMTP dans le code**
- ✅ Utiliser les variables d'environnement pour les informations sensibles
- ✅ Le dossier `sync_results/` peut contenir des données sensibles, s'assurer qu'il n'est pas accessible publiquement
