#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour ajouter l'autorisation du matricule 378 pour la section "Rapports CQ".

1. Identifie ou crée la section "Rapports CQ" dans WEB_SECTIONS (Projet 10)
2. Identifie ou crée l'action "Consultation" dans WEB_ACTIONS pour cette section
3. Insère dans WEB_DROITS_ACCES (Matricule=378, ID_Action, Autorise=1)

Si la section "Rapports CQ" n'existe pas, elle sera créée.
"""
from db import get_db_cursor

MATRICULE = 378
AUTORISE = 1
NOM_SECTION = "Rapports CQ"
NOM_ACTION = "Consultation"


def main():
    print("=" * 70)
    print("AUTORISATION RAPPORTS CQ - Matricule 378")
    print("=" * 70)
    print()

    try:
        with get_db_cursor() as cursor:
            # Obtenir ID_Proj du Projet 10
            cursor.execute(
                "SELECT ID FROM WEB_PROJETS WHERE NumProj = 10 OR ID = 10"
            )
            proj = cursor.fetchone()
            if not proj:
                print("[ERREUR] Projet 10 introuvable dans WEB_PROJETS.")
                return False
            id_proj = proj.ID

            # 1. Identifier ou créer la section "Rapports CQ"
            print(f"1. Section '{NOM_SECTION}' dans WEB_SECTIONS...")
            cursor.execute(
                """SELECT ID, Nom FROM WEB_SECTIONS
                   WHERE ID_Proj = ? AND (Nom = ? OR LOWER(Nom) = LOWER(?))""",
                (id_proj, NOM_SECTION, NOM_SECTION),
            )
            section = cursor.fetchone()
            if section:
                id_section = section.ID
                print(f"   [OK] Section existante: ID={id_section}, Nom='{section.Nom}'")
            else:
                cursor.execute(
                    """INSERT INTO WEB_SECTIONS (Nom, ID_Proj) OUTPUT INSERTED.ID
                       VALUES (?, ?)""",
                    (NOM_SECTION, id_proj),
                )
                id_section = cursor.fetchone()[0]
                cursor.connection.commit()
                print(f"   [OK] Section créée: ID={id_section}, Nom='{NOM_SECTION}'")
            print()

            # 2. Identifier ou créer l'action "Consultation"
            print(f"2. Action '{NOM_ACTION}' dans WEB_ACTIONS...")
            cursor.execute(
                """SELECT ID, Action FROM WEB_ACTIONS
                   WHERE ID_Section = ? AND (Action = ? OR UPPER(Action) = UPPER(?))""",
                (id_section, NOM_ACTION, NOM_ACTION),
            )
            action = cursor.fetchone()
            if action:
                id_action = action.ID
                print(f"   [OK] Action existante: ID_Action={id_action}, Action='{action.Action}'")
            else:
                cursor.execute(
                    """INSERT INTO WEB_ACTIONS (Action, ID_Section) VALUES (?, ?)""",
                    (NOM_ACTION, id_section),
                )
                cursor.connection.commit()
                cursor.execute(
                    """SELECT ID FROM WEB_ACTIONS WHERE ID_Section = ? AND Action = ?""",
                    (id_section, NOM_ACTION),
                )
                row = cursor.fetchone()
                id_action = int(row.ID) if row else None
                if not id_action:
                    print("   [ERREUR] Action insérée mais ID non récupéré.")
                    return False
                print(f"   [OK] Action créée: ID_Action={id_action}, Action='{NOM_ACTION}'")
                print(f"   [OK] Action créée: ID_Action={id_action}, Action='{NOM_ACTION}'")
            print()

            # 3. Vérifier le matricule
            print("3. Vérification du matricule 378...")
            cursor.execute(
                "SELECT Matricule, Nom, Prenom FROM personel WHERE Matricule = ?",
                (MATRICULE,),
            )
            emp = cursor.fetchone()
            if not emp:
                print(f"   [ERREUR] Le matricule {MATRICULE} n'existe pas dans personel.")
                return False
            print(f"   [OK] {emp.Nom} {emp.Prenom}")
            print()

            # 4. Insérer dans WEB_DROITS_ACCES si pas déjà présent
            print("4. Insertion dans WEB_DROITS_ACCES...")
            cursor.execute(
                """SELECT 1 FROM WEB_DROITS_ACCES
                   WHERE Matricule = ? AND ID_Action = ?""",
                (MATRICULE, id_action),
            )
            if cursor.fetchone():
                print(f"   [INFO] Le matricule {MATRICULE} a déjà l'autorisation (ID_Action={id_action}).")
                return True

            cursor.execute(
                """INSERT INTO WEB_DROITS_ACCES (Matricule, ID_Action, Autorise)
                   VALUES (?, ?, ?)""",
                (MATRICULE, id_action, AUTORISE),
            )
            cursor.connection.commit()
            print(f"   [SUCCES] Matricule {MATRICULE}, ID_Action {id_action}, Autorise=1")
            print()
            print("=" * 70)
            return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ok = main()
    raise SystemExit(0 if ok else 1)
