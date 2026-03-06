#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exécute la création de l'action DEBLOQUER (ID=33, ID_Section=2)
et accorde l'accès aux matricules 167, 268, 32 dans WEB_DROITS_ACCES.
À lancer depuis la racine du projet : python scripts/exec_creer_action_debloquer_id33.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_db_cursor


def main():
    print("Création action DEBLOQUER (ID=33) et droits pour 167, 268, 32...")
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1 FROM dbo.WEB_ACTIONS WHERE ID = 33")
            exists = cursor.fetchone()
            if not exists:
                cursor.execute("SET IDENTITY_INSERT dbo.WEB_ACTIONS ON")
                cursor.execute("""
                    INSERT INTO dbo.WEB_ACTIONS (ID, ID_Section, Action, archive, CodeProj, Nom_SECTIONS)
                    VALUES (33, 2, 'DEBLOQUER', 0, 'Projet 11', 'Liste des Traitements')
                """)
                cursor.execute("SET IDENTITY_INSERT dbo.WEB_ACTIONS OFF")
                print("  Action DEBLOQUER créée (ID=33, ID_Section=2).")
            else:
                cursor.execute("""
                    UPDATE dbo.WEB_ACTIONS
                    SET ID_Section = 2, Action = 'DEBLOQUER', archive = 0,
                        CodeProj = 'Projet 11', Nom_SECTIONS = 'Liste des Traitements'
                    WHERE ID = 33
                """)
                print("  Action ID=33 déjà existante, mise à jour effectuée.")

            for matricule in (167, 268, 32):
                cursor.execute(
                    "SELECT 1 FROM dbo.WEB_DROITS_ACCES WHERE Matricule = ? AND ID_Action = 33",
                    (matricule,),
                )
                if cursor.fetchone():
                    cursor.execute(
                        "UPDATE dbo.WEB_DROITS_ACCES SET Autorise = 1, NomAtelier = NULL WHERE Matricule = ? AND ID_Action = 33",
                        (matricule,),
                    )
                else:
                    cursor.execute(
                        "INSERT INTO dbo.WEB_DROITS_ACCES (Matricule, NomAtelier, ID_Action, Autorise) VALUES (?, NULL, 33, 1)",
                        (matricule,),
                    )
            cursor.connection.commit()
        print("  Droits DEBLOQUER (ID_Action=33) accordés aux matricules 167, 268, 32.")
        print("Fin.")
        return True
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
