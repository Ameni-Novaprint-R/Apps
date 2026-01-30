#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Insertion des sections du Projet 11 (Gestion des Traitements) dans WEB_SECTIONS.

Sections ajoutées :
- Nouvelle fiche de production
- Liste des Traitements
- Statistiques

Utilise la configuration de db.py. Idempotent : pas de doublon si re-exécution.
Au démarrage : ajoute la contrainte UQ (ID_Proj, Nom) si elle manque
(évite deux sections de même nom dans un même projet).
"""

from db import get_db_cursor

# Si la table n'existe pas, on appelle creer_table_web_sections (crée table + UQ)
try:
    from creer_table_web_sections import creer_table_web_sections
except ImportError:
    creer_table_web_sections = None

SECTIONS_PROJET_11 = [
    'Nouvelle fiche de production',
    'Liste des Traitements',
    'Statistiques',
]


def inserer_sections_projet11():
    """Insère les sections du Projet 11 dans WEB_SECTIONS (si elles n'existent pas)."""
    print("=" * 70)
    print("Insertion des sections du Projet 11 dans WEB_SECTIONS")
    print("=" * 70)
    print()

    try:
        with get_db_cursor() as cursor:
            # Si la table n'existe pas : créer table + UQ (ID_Proj, Nom) via creer_table_web_sections
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_SECTIONS'
            """)
            if cursor.fetchone()[0] == 0:
                if creer_table_web_sections:
                    print("[INFO] Table WEB_SECTIONS absente. Creation (avec UQ ID_Proj, Nom)...")
                    creer_table_web_sections()
                    print()
                    import inserer_sections_projet11 as _m
                    return _m.inserer_sections_projet11()
                else:
                    print("[ERREUR] Table WEB_SECTIONS absente. Exécutez: python creer_table_web_sections.py")
                    return False

            # Appliquer la contrainte UNIQUE (ID_Proj, Nom) si elle n'existe pas
            cursor.execute("""
                SELECT COUNT(*) FROM sys.key_constraints
                WHERE name = 'UQ_WEB_SECTIONS_ID_Proj_Nom' AND parent_object_id = OBJECT_ID('dbo.WEB_SECTIONS')
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    ALTER TABLE dbo.WEB_SECTIONS ADD CONSTRAINT UQ_WEB_SECTIONS_ID_Proj_Nom UNIQUE (ID_Proj, Nom)
                """)
                cursor.connection.commit()
                print("[INFO] Contrainte UQ_WEB_SECTIONS_ID_Proj_Nom (éviter 2 sections même nom/projet) ajoutée.")
                print()

            cursor.execute("SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = 11")
            row = cursor.fetchone()
            if not row:
                print("[ERREUR] Projet 11 introuvable dans WEB_PROJETS.")
                return False
            id_proj = row.ID

            for nom in SECTIONS_PROJET_11:
                cursor.execute(
                    """
                    INSERT INTO dbo.WEB_SECTIONS (ID_Proj, Nom, archive)
                    SELECT ?, ?, 0
                    WHERE NOT EXISTS (SELECT 1 FROM dbo.WEB_SECTIONS WHERE ID_Proj = ? AND Nom = ?)
                    """,
                    (id_proj, nom, id_proj, nom),
                )
                if cursor.rowcount > 0:
                    print(f"  + {nom}")
                else:
                    print(f"  (déjà présente) {nom}")

            cursor.connection.commit()

            print()
            print("Sections du Projet 11 dans WEB_SECTIONS :")
            cursor.execute(
                """
                SELECT s.ID, s.ID_Proj, p.NumProj, p.CodeProj, s.Nom, s.archive
                FROM dbo.WEB_SECTIONS s
                INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
                WHERE s.ID_Proj = ?
                ORDER BY s.ID
                """,
                (id_proj,),
            )
            for r in cursor.fetchall():
                print(f"   ID={r.ID}  ID_Proj={r.ID_Proj}  NumProj={r.NumProj}  {r.CodeProj}  |  {r.Nom}  archive={r.archive}")

            print()
            print("=" * 70)
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        try:
            cursor.connection.rollback()
        except Exception:
            pass
        return False
    return True


if __name__ == "__main__":
    inserer_sections_projet11()
