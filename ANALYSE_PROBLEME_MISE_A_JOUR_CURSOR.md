# Analyse : Problème après mise à jour Cursor 2.4.21

## Constat

- **Avant la mise à jour** : Les scripts SQL s'exécutaient normalement depuis le terminal Cursor
- **Après la mise à jour** (version 2.4.21, 22 janvier 2026) : Erreur "Sandbox cannot run from an elevated administrator process"
- **Même compte Windows**, même méthode de lancement, **seule la mise à jour a changé**

## Cause probable

La version **2.4.21** a introduit des **changements de sécurité** (mentionnés dans le changelog : "Linux sandboxing for agents", améliorations de sécurité). Ces changements ont probablement renforcé la vérification qui bloque l'exécution de commandes quand le processus est détecté comme "élevé", **même si le sandbox est désactivé** dans `settings.json`.

## Solutions possibles

### Solution 1 : Revenir à une version antérieure (si disponible)

1. Désinstaller Cursor 2.4.21
2. Télécharger et installer une version antérieure (avant 2.4)
3. Désactiver les mises à jour automatiques dans Cursor

**Limitation** : Les versions antérieures peuvent ne plus être disponibles sur le site de Cursor.

### Solution 2 : Utiliser la route web (recommandé)

La route web fonctionne **indépendamment** de la version de Cursor car les scripts s'exécutent dans le processus Flask, pas dans Cursor.

**Avantages** :
- ✅ Fonctionne avec toutes les versions de Cursor
- ✅ Fonctionne même si Cursor est en admin
- ✅ Sandbox Cursor non concerné

**Utilisation** :
- Script automatique : `Lancer_Init_Web_Tables_Auto.bat`
- Ou manuel : `python app.py` → navigateur → `http://localhost:5000/admin/init-web-tables`

### Solution 3 : Attendre un correctif de Cursor

Signaler le problème à Cursor (forum, GitHub) et attendre une mise à jour qui corrige ce comportement.

## Paramètres actuels dans settings.json

```json
{
    "window.commandCenter": true,
    "chat.sandboxEnabled": false,
    "experimental.legacyTerminalTool": true,
    "chat.autoRun": "runEverything"
}
```

**Résultat** : Le sandbox est désactivé, mais Cursor **refuse quand même** d'exécuter des commandes quand le processus est détecté comme élevé. C'est une **vérification supplémentaire** introduite dans la version 2.4.21 qui ne peut pas être contournée par les paramètres.

## Conclusion

La mise à jour 2.4.21 a introduit une **restriction de sécurité supplémentaire** qui ne peut pas être désactivée via `settings.json`. Cette restriction est **intentionnelle** et fait partie des améliorations de sécurité de Cursor.

**Solution pratique** : Utiliser la route web pour exécuter les scripts SQL. C'est la méthode la plus fiable et elle fonctionne indépendamment de la version de Cursor ou de son mode d'exécution.
