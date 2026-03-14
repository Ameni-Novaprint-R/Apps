#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer la section "Gestion des droits d'accès" dans le Projet 22
et l'action ADMINISTRATION associée.
- Insère dans WEB_SECTIONS si la section n'existe pas
- Insère dans WEB_ACTIONS l'action ADMINISTRATION si elle n'existe pas
"""
from db import get_db_cursor

NOM_SECTION = "Gestion des droits d'accès"
NOM_ACTION = "ADMINISTRATION"
NUM_PROJET = 22


def run():
    with get_db_cursor() as cursor:
        # ID du projet 22
        cursor.execute("SELECT ID FROM [dbo].[WEB_PROJETS] WHERE NumProj = ? OR ID = ?", (NUM_PROJET, NUM_PROJET))
        row = cursor.fetchone()
        if not row:
            print("[ERREUR] Projet 22 introuvable dans WEB_PROJETS.")
            return False
        id_proj = row.ID

        # Section
        cursor.execute(
            """SELECT ID FROM [dbo].[WEB_SECTIONS] WHERE ID_Proj = ? AND (Nom = ? OR LOWER(Nom) = LOWER(?))""",
            (id_proj, NOM_SECTION, NOM_SECTION),
        )
        sec = cursor.fetchone()
        if sec:
            id_section = sec.ID
            print(f"[OK] Section existante: ID={id_section}")
        else:
            cursor.execute(
                """INSERT INTO [dbo].[WEB_SECTIONS] (ID_Proj, Nom, archive)
                   OUTPUT INSERTED.ID VALUES (?, ?, 0)""",
                (id_proj, NOM_SECTION),
            )
            row = cursor.fetchone()
            id_section = row[0] if row else None
            cursor.connection.commit()
            if not id_section:
                print("[ERREUR] ID de section non récupéré.")
                return False
            print(f"[OK] Section créée: ID={id_section}, Nom='{NOM_SECTION}'")

        # Action
        cursor.execute(
            """SELECT ID FROM [dbo].[WEB_ACTIONS] WHERE ID_Section = ? AND (Action = ? OR UPPER(Action) = UPPER(?))""",
            (id_section, NOM_ACTION, NOM_ACTION),
        )
        act = cursor.fetchone()
        id_action = None
        if act:
            id_action = act.ID
            print(f"[OK] Action existante: ID={act.ID}, Action='{NOM_ACTION}'")
        else:
            cursor.execute(
                """INSERT INTO [dbo].[WEB_ACTIONS] (ID_Section, Action, archive, CodeProj, Nom_SECTIONS)
                   VALUES (?, ?, 0, 'Projet 22', ?)""",
                (id_section, NOM_ACTION, NOM_SECTION),
            )
            cursor.connection.commit()
            cursor.execute(
                """SELECT ID FROM [dbo].[WEB_ACTIONS] WHERE ID_Section = ? AND Action = ?""",
                (id_section, NOM_ACTION),
            )
            row = cursor.fetchone()
            id_action = row[0] if row else None
            print(f"[OK] Action créée: ID={id_action}, Action='{NOM_ACTION}'")

        # Accorder l'action aux super-utilisateurs (1, 179, 321) s'ils n'ont pas déjà le droit
        if id_action:
            for mat in [1, 179, 321]:
                cursor.execute(
                    "SELECT 1 FROM [dbo].[WEB_DROITS_ACCES] WHERE Matricule = ? AND ID_Action = ?",
                    (mat, id_action)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        """INSERT INTO [dbo].[WEB_DROITS_ACCES] (Matricule, NomAtelier, ID_Action, Autorise)
                           VALUES (?, NULL, ?, 1)""",
                        (mat, id_action)
                    )
                    print(f"[OK] Droit accordé au matricule {mat}")
            cursor.connection.commit()

    print("Terminé.")
    return True


if __name__ == "__main__":
    run()
