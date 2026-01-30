# Corriger : « Sandbox cannot run from an elevated administrator process »

Quand Cursor est lancé **en tant qu’administrateur**, le terminal (et l’Agent) ne peut pas exécuter de commandes :  
`Sandbox cannot run from an elevated administrator process. Please run Cursor without administrator privileges.`

**Il n'existe pas de réglage dans la fenêtre Cursor** pour enlever le mode admin. Il faut agir sur le raccourci, le .exe, ou utiliser le lanceur ci-dessous.

---

## Si le raccourci affiche déjà « décoché » mais Cursor est encore en admin

Causes possibles : **(1)** le **fichier Cursor.exe** force l’admin, **(2)** un **autre raccourci** est utilisé (barre des tâches, Démarrer), **(3)** l’**Explorateur** est en admin.

### A. Vérifier Cursor.exe

1. **Fermer Cursor**
2. Trouver **Cursor.exe** : `C:\Users\VOTRE_UTILISATEUR\AppData\Local\Programs\cursor\Cursor.exe` ou Menu Démarrer → Cursor → clic droit → **Emplacement du fichier**
3. **Clic droit sur Cursor.exe** → **Propriétés** → **Compatibilité**
4. **Décocher** « Exécuter ce programme en tant qu’administrateur »
5. S’il y a **« Modifier les paramètres pour tous les utilisateurs »** : cliquer, décocher aussi, Appliquer, OK
6. **Appliquer** → **OK**

### B. Utiliser le lanceur « sans admin »

Le script **`Lancer_Cursor_Sans_Admin.vbs`** utilise `__COMPAT_LAYER=RunAsInvoker` pour forcer Cursor à ne pas s'élever (même si le manifeste le demande).  
Copier ce fichier sur le Bureau, fermer Cursor, puis **double-clic sur le .vbs** pour l’ouvrir. Si Cursor est ailleurs, éditer le .vbs et adapter la ligne `chemin`.

**Alternative (une seule fois) :** exécuter **`Forcer_Cursor_Sans_Admin_Registre.bat`** pour ajouter RUNASINVOKER dans le registre. Ensuite, Cursor pourra être lancé normalement (raccourci, Démarrer) sans s'élever.

### C. Autres vérifications

- Ne pas lancer Cursor via **« Exécuter en tant qu’administrateur »** ou depuis une **invite en admin**
- Si l’Explorateur est en admin, tout ce que vous ouvrez peut être élevé : redémarrer l’Explorateur en mode normal ou redémarrer la session

---

## Solution classique : ne plus lancer Cursor en administrateur

### 1. Désactiver « Exécuter en tant qu’administrateur » sur le raccourci

1. **Fermer Cursor**
2. **Clic droit** sur le raccourci Cursor (Bureau, menu Démarrer ou barre des tâches) → **Propriétés**
3. Onglet **Compatibilité**
4. **Décocher** : « Exécuter ce programme en tant qu’administrateur »
5. **Appliquer** → **OK**

### 2. Relancer Cursor normalement

- **Double-clic** sur le raccourci (sans « Exécuter en tant qu’administrateur »)
- Ne plus utiliser « Clic droit → Exécuter en tant qu’administrateur »

### 3. Vérifier

Dans Cursor, ouvrir un terminal (Ctrl+ù ou Terminal > New Terminal) et lancer :

```powershell
cd c:\Apps
python creer_table_web_projets.py
```

Si tout est correct, le script s’exécute sans l’erreur sandbox.

---

## Si le raccourci est dans Program Files (ou un dossier protégé)

Le raccourci peut être en lecture seule. Dans ce cas :

- Créer un **nouveau raccourci** sur le Bureau vers `Cursor.exe`
- Dans les propriétés de ce nouveau raccourci, onglet **Compatibilité** : s’assurer que « Exécuter ce programme en tant qu’administrateur » est **décoché**
- Utiliser **ce** raccourci pour lancer Cursor

---

## Si vous devez garder Cursor en admin pour d’autres raisons

Dans ce cas, les commandes du terminal Cursor resteront bloquées. Il faut alors :

- soit exécuter les scripts **en dehors de Cursor** (PowerShell, Invite de commandes, double‑clic sur les `.bat`) ;
- soit utiliser la **route d’admin** de l’app Flask :  
  **http://localhost:5000/admin/init-web-tables**  
  (les scripts sont exécutés par le processus Python de l’app, pas par le terminal Cursor).
