"""
Script pour configurer les droits d'accès du Projet 1
- Créer les 3 sections dans WEB_SECTIONS
- Créer l'action "Accès" pour chaque section dans WEB_ACTIONS
- Donner les droits au matricule 397 pour ces 3 actions
"""
from db import get_db_cursor

# Configuration
ID_PROJET = 1  # Projet 1
MATRICULE = 397  # Matricule à autoriser
NOM_ACTION = "Accès"  # Nom de l'action unique pour chaque section

# Les 3 sections du projet 1
SECTIONS = [
    "Calendrier des Dossiers à Livrer",
    "Suivi des Dossiers et des Délais de Livraison",
    "Performance"
]

def get_or_create_section(cursor, id_proj, nom_section):
    """Récupère ou crée une section dans WEB_SECTIONS"""
    cursor.execute(
        "SELECT ID FROM WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?",
        (id_proj, nom_section)
    )
    row = cursor.fetchone()
    if row:
        return row.ID
    
    # Créer la section
    cursor.execute(
        "INSERT INTO WEB_SECTIONS (ID_Proj, Nom, archive) VALUES (?, ?, 0)",
        (id_proj, nom_section)
    )
    cursor.execute(
        "SELECT ID FROM WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?",
        (id_proj, nom_section)
    )
    row = cursor.fetchone()
    if not row:
        raise RuntimeError(f"Impossible de retrouver la section créée: {nom_section}")
    return row.ID

def get_or_create_action(cursor, id_section, nom_action, code_proj, nom_section):
    """Récupère ou crée une action dans WEB_ACTIONS"""
    cursor.execute(
        "SELECT ID FROM WEB_ACTIONS WHERE ID_Section = ? AND Action = ?",
        (id_section, nom_action)
    )
    row = cursor.fetchone()
    if row:
        return row.ID
    
    # Créer l'action
    cursor.execute(
        """
        INSERT INTO WEB_ACTIONS (ID_Section, Action, archive, CodeProj, Nom_SECTIONS)
        VALUES (?, ?, 0, ?, ?)
        """,
        (id_section, nom_action, code_proj, nom_section)
    )
    cursor.execute(
        "SELECT ID FROM WEB_ACTIONS WHERE ID_Section = ? AND Action = ?",
        (id_section, nom_action)
    )
    row = cursor.fetchone()
    if not row:
        raise RuntimeError(f"Impossible de retrouver l'action créée: {nom_action}")
    return row.ID

def setup_projet1_rights():
    try:
        with get_db_cursor() as cursor:
            print("=" * 80)
            print("CONFIGURATION DES DROITS D'ACCES - PROJET 1")
            print("=" * 80)
            print()
            
            # ÉTAPE 1: Vérifier que le projet 1 existe
            print("ETAPE 1: Verification du projet 1...")
            cursor.execute("SELECT ID, NumProj, Nom FROM WEB_PROJETS WHERE ID = ? OR NumProj = ?", (ID_PROJET, ID_PROJET))
            projet = cursor.fetchone()
            if not projet:
                print(f"[ERREUR] Le projet 1 n'existe pas dans WEB_PROJETS")
                return False
            
            id_projet = projet.ID
            code_proj = f"Projet {projet.NumProj}"
            print(f"[OK] Projet trouve: ID={id_projet}, NumProj={projet.NumProj}, Nom={projet.Nom}")
            print()
            
            # ÉTAPE 2: Vérifier que le matricule 397 existe
            print("ETAPE 2: Verification du matricule 397...")
            cursor.execute("SELECT Matricule, Nom, Prenom FROM personel WHERE Matricule = ?", (MATRICULE,))
            emp = cursor.fetchone()
            if not emp:
                print(f"[ERREUR] Le matricule {MATRICULE} n'existe pas dans personel")
                return False
            print(f"[OK] Matricule {MATRICULE} trouve: {emp.Nom} {emp.Prenom}")
            print()
            
            # ÉTAPE 3: Créer ou récupérer les sections
            print("ETAPE 3: Creation/recuperation des sections...")
            sections_created = {}
            for nom_section in SECTIONS:
                id_section = get_or_create_section(cursor, id_projet, nom_section)
                sections_created[nom_section] = id_section
                print(f"  [OK] Section '{nom_section}': ID={id_section}")
            print()
            
            # ÉTAPE 4: Créer ou récupérer les actions "Accès" pour chaque section
            print("ETAPE 4: Creation/recuperation des actions 'Accès'...")
            actions_created = {}
            for nom_section, id_section in sections_created.items():
                id_action = get_or_create_action(cursor, id_section, NOM_ACTION, code_proj, nom_section)
                actions_created[nom_section] = id_action
                print(f"  [OK] Action '{NOM_ACTION}' pour section '{nom_section}': ID={id_action}")
            print()
            
            # ÉTAPE 5: Donner les droits au matricule 397
            print(f"ETAPE 5: Attribution des droits au matricule {MATRICULE}...")
            droits_ajoutes = []
            droits_deja_presents = []
            
            for nom_section, id_action in actions_created.items():
                # Vérifier si le droit existe déjà
                cursor.execute(
                    "SELECT ID FROM WEB_DROITS_ACCES WHERE Matricule = ? AND ID_Action = ?",
                    (MATRICULE, id_action)
                )
                existe = cursor.fetchone()
                
                if existe:
                    droits_deja_presents.append((nom_section, id_action))
                    print(f"  [INFO] Droit deja present: Matricule {MATRICULE} -> Action ID {id_action} ({nom_section})")
                else:
                    cursor.execute(
                        "INSERT INTO WEB_DROITS_ACCES (Matricule, ID_Action, Autorise) VALUES (?, ?, 1)",
                        (MATRICULE, id_action)
                    )
                    droits_ajoutes.append((nom_section, id_action))
                    print(f"  [OK] Droit ajoute: Matricule {MATRICULE} -> Action ID {id_action} ({nom_section})")
            
            cursor.connection.commit()
            print()
            
            # Résumé
            print("=" * 80)
            print("RESUME")
            print("=" * 80)
            print(f"Sections creees/trouvees: {len(sections_created)}")
            for nom, id_s in sections_created.items():
                print(f"  - {nom}: ID={id_s}")
            print()
            print(f"Actions creees/trouvees: {len(actions_created)}")
            for nom, id_a in actions_created.items():
                print(f"  - Action '{NOM_ACTION}' pour '{nom}': ID={id_a}")
            print()
            print(f"Droits ajoutes: {len(droits_ajoutes)}")
            print(f"Droits deja presents: {len(droits_deja_presents)}")
            print("=" * 80)
            
            return True
            
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = setup_projet1_rights()
    if success:
        print("\n[SUCCES] Configuration terminee avec succes!")
    else:
        print("\n[ERREUR] Configuration echouee!")
    raise SystemExit(0 if success else 1)
