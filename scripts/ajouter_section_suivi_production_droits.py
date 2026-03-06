#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Section Suivi Production - Projet 11 : identifier dans WEB_SECTIONS, 
créer action CONSULTATION dans WEB_ACTIONS, et accorder les droits.

Droits :
- Matricules : 167, 268, 397
- Ateliers : Atelier1 à Atelier10
"""

from db import get_db_cursor

MATRICULES = [167, 268, 397]
NOMS_ATELIERS = [f"Atelier{i}" for i in range(1, 11)]


def main():
    print("=" * 70)
    print("Section Suivi Production – Projet 11 – Configuration des droits")
    print("=" * 70)

    try:
        with get_db_cursor() as cursor:
            # 1. Projet 11
            cursor.execute("SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = 11")
            proj = cursor.fetchone()
            if not proj:
                print("[ERREUR] Projet 11 introuvable dans WEB_PROJETS.")
                return False
            id_proj = proj.ID
            print(f"[OK] Projet 11 (ID={id_proj})")

            # 2. Section Suivi Production (créer si absente)
            cursor.execute("""
                SELECT ID FROM dbo.WEB_SECTIONS
                WHERE ID_Proj = ? AND Nom = 'Suivi Production'
            """, (id_proj,))
            section = cursor.fetchone()
            if section:
                id_section = section.ID
                print(f"[OK] Section 'Suivi Production' déjà présente (ID={id_section})")
            else:
                cursor.execute("""
                    INSERT INTO dbo.WEB_SECTIONS (ID_Proj, Nom, archive)
                    VALUES (?, 'Suivi Production', 0)
                """, (id_proj,))
                cursor.execute("SELECT ID FROM dbo.WEB_SECTIONS WHERE ID_Proj = ? AND Nom = 'Suivi Production'", (id_proj,))
                r = cursor.fetchone()
                id_section = r.ID if r else None
                if not id_section:
                    print("[ERREUR] Impossible de récupérer l'ID de la section après INSERT.")
                    return False
                print(f"[OK] Section 'Suivi Production' créée (ID={id_section})")

            # 3. Action CONSULTATION (créer si absente)
            cursor.execute("""
                SELECT ID FROM dbo.WEB_ACTIONS
                WHERE ID_Section = ? AND Action = 'CONSULTATION'
            """, (id_section,))
            row = cursor.fetchone()
            if row:
                id_action = row.ID
                print(f"[OK] Action CONSULTATION déjà présente (ID_Action={id_action})")
            else:
                cursor.execute("""
                    INSERT INTO dbo.WEB_ACTIONS (ID_Section, Action, archive, CodeProj, Nom_SECTIONS)
                    VALUES (?, 'CONSULTATION', 0, 'Projet 11', 'Suivi Production')
                """, (id_section,))
                cursor.execute("SELECT ID FROM dbo.WEB_ACTIONS WHERE ID_Section = ? AND Action = 'CONSULTATION'", (id_section,))
                r2 = cursor.fetchone()
                id_action = r2.ID if r2 else None
                if not id_action:
                    print("[ERREUR] Impossible de récupérer l'ID de l'action CONSULTATION après INSERT.")
                    return False
                print(f"[OK] Action CONSULTATION créée (ID_Action={id_action})")

            # 4. Droits pour matricules 167, 268, 397
            ins_mat = 0
            for matricule in MATRICULES:
                cursor.execute("""
                    SELECT 1 FROM dbo.WEB_DROITS_ACCES
                    WHERE Matricule = ? AND ID_Action = ?
                """, (matricule, id_action))
                if cursor.fetchone():
                    continue
                cursor.execute("""
                    INSERT INTO dbo.WEB_DROITS_ACCES (Matricule, NomAtelier, ID_Action, Autorise)
                    VALUES (?, NULL, ?, 1)
                """, (matricule, id_action))
                ins_mat += 1
                print(f"  + Droit CONSULTATION pour matricule {matricule}")
            if ins_mat == 0 and MATRICULES:
                print("  (matricules 167, 268, 397 : droits déjà présents)")

            # 5. Droits pour ateliers Atelier1 à Atelier10
            ins_at = 0
            for nom_atelier in NOMS_ATELIERS:
                cursor.execute("""
                    SELECT 1 FROM dbo.WEB_DROITS_ACCES
                    WHERE NomAtelier = ? AND ID_Action = ? AND (Matricule IS NULL OR Matricule = 0)
                """, (nom_atelier, id_action))
                if cursor.fetchone():
                    continue
                cursor.execute("""
                    INSERT INTO dbo.WEB_DROITS_ACCES (Matricule, NomAtelier, ID_Action, Autorise)
                    VALUES (NULL, ?, ?, 1)
                """, (nom_atelier, id_action))
                ins_at += 1
                print(f"  + Droit CONSULTATION pour {nom_atelier}")
            if ins_at == 0:
                print("  (ateliers Atelier1..Atelier10 : droits déjà présents)")

            cursor.connection.commit()
            print()
            print(f"Récapitulatif : Section ID={id_section}, Action CONSULTATION ID={id_action}")
            print(f"  Matricules ajoutés : {ins_mat} | Ateliers ajoutés : {ins_at}")
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
    ok = main()
    raise SystemExit(0 if ok else 1)
