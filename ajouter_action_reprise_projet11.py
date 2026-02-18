#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ajoute l'action REPRISE pour le Projet 11, section « Liste des Traitements » :

1. WEB_ACTIONS : une ligne Action = 'REPRISE', CodeProj = 'Projet 11', Nom_SECTIONS = 'Liste des Traitements'
2. WEB_DROITS_ACCES : droit pour les 10 ateliers (NomAtelier = Atelier1..Atelier10, Autorise = 1)

Idempotent : pas de doublon si re-exécution.
Utilise la configuration de db.py.
"""

from db import get_db_cursor


def main():
    print("=" * 70)
    print("Ajout action REPRISE – Projet 11, section Liste des Traitements")
    print("=" * 70)

    try:
        with get_db_cursor() as cursor:
            # ID du projet 11
            cursor.execute("SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = 11")
            proj = cursor.fetchone()
            if not proj:
                print("[ERREUR] Projet 11 introuvable dans WEB_PROJETS.")
                return False
            id_proj = proj.ID

            # Section « Liste des Traitements »
            cursor.execute("""
                SELECT ID FROM dbo.WEB_SECTIONS
                WHERE ID_Proj = ? AND Nom = 'Liste des Traitements'
            """, (id_proj,))
            section = cursor.fetchone()
            if not section:
                print("[ERREUR] Section 'Liste des Traitements' introuvable pour le Projet 11.")
                return False
            id_section = section.ID

            # Id de l'action REPRISE (création si besoin)
            cursor.execute("""
                SELECT ID FROM dbo.WEB_ACTIONS
                WHERE ID_Section = ? AND Action = 'REPRISE'
            """, (id_section,))
            row = cursor.fetchone()
            if row:
                id_action_reprise = row.ID
                print(f"[OK] Action REPRISE déjà présente (ID_Action = {id_action_reprise})")
            else:
                cursor.execute("""
                    INSERT INTO dbo.WEB_ACTIONS (ID_Section, Action, archive, CodeProj, Nom_SECTIONS)
                    VALUES (?, 'REPRISE', 0, 'Projet 11', 'Liste des Traitements')
                """, (id_section,))
                cursor.execute("SELECT ID FROM dbo.WEB_ACTIONS WHERE ID_Section = ? AND Action = 'REPRISE'", (id_section,))
                r2 = cursor.fetchone()
                id_action_reprise = r2.ID if r2 else None
                if not id_action_reprise:
                    print("[ERREUR] Impossible de récupérer l'ID de l'action REPRISE après INSERT.")
                    return False
                print(f"[OK] Action REPRISE créée (ID_Action = {id_action_reprise})")

            # Droits pour les 10 ateliers
            inserted = 0
            for i in range(1, 11):
                nom_atelier = f"Atelier{i}"
                cursor.execute("""
                    SELECT 1 FROM dbo.WEB_DROITS_ACCES
                    WHERE NomAtelier = ? AND ID_Action = ? AND (Matricule IS NULL OR Matricule = 0)
                """, (nom_atelier, id_action_reprise))
                if cursor.fetchone():
                    continue
                cursor.execute("""
                    INSERT INTO dbo.WEB_DROITS_ACCES (Matricule, NomAtelier, ID_Action, Autorise)
                    VALUES (NULL, ?, ?, 1)
                """, (nom_atelier, id_action_reprise))
                inserted += 1
                print(f"  + Droit REPRISE pour {nom_atelier}")

            # Droits pour les matricules qui ont déjà MODIFICATION (ID_Action = 3)
            cursor.execute("""
                SELECT DISTINCT Matricule FROM dbo.WEB_DROITS_ACCES
                WHERE ID_Action = 3 AND Matricule IS NOT NULL AND Autorise = 1
            """)
            matricules = [row.Matricule for row in cursor.fetchall()]
            inserted_mat = 0
            for mat in matricules:
                cursor.execute("""
                    SELECT 1 FROM dbo.WEB_DROITS_ACCES
                    WHERE Matricule = ? AND ID_Action = ?
                """, (mat, id_action_reprise))
                if cursor.fetchone():
                    continue
                cursor.execute("""
                    INSERT INTO dbo.WEB_DROITS_ACCES (Matricule, NomAtelier, ID_Action, Autorise)
                    VALUES (?, NULL, ?, 1)
                """, (mat, id_action_reprise))
                inserted_mat += 1
            if inserted_mat:
                print(f"  + Droit REPRISE pour {inserted_mat} matricule(s) (MODIFICATION)")

            cursor.connection.commit()
            print()
            print(f"Récapitulatif : ID_Action REPRISE = {id_action_reprise}, {inserted} atelier(s), {inserted_mat} matricule(s).")
            print("=" * 70)
            return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        try:
            cursor.connection.rollback()
        except Exception:
            pass
        return False


if __name__ == "__main__":
    main()
