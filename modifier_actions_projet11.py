#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Modification des actions du Projet 11 dans WEB_DROITS_ACCES.

1. Archiver (supprimer) EXPORT_EXCEL et EXPORT_PDF de la section Statistiques
2. Ajouter EXPORT_EXCEL et EXPORT_PDF à la section Liste des Traitements

Utilise la configuration de db.py. Idempotent : pas de doublon si re-exécution.
"""

from db import get_db_cursor


def modifier_actions_projet11():
    """Modifie les actions du Projet 11 dans WEB_DROITS_ACCES."""
    print("=" * 70)
    print("Modification des actions du Projet 11 dans WEB_DROITS_ACCES")
    print("=" * 70)
    print()

    try:
        with get_db_cursor() as cursor:
            # Vérifier que la table WEB_DROITS_ACCES existe
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_DROITS_ACCES'
            """)
            if cursor.fetchone()[0] == 0:
                print("[ERREUR] La table WEB_DROITS_ACCES n'existe pas.")
                return False

            # Récupérer l'ID du Projet 11
            cursor.execute("SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = 11")
            proj_row = cursor.fetchone()
            if not proj_row:
                print("[ERREUR] Projet 11 introuvable dans WEB_PROJETS.")
                return False
            id_proj = proj_row.ID

            # ============================================================
            # ÉTAPE 1: Archiver EXPORT_EXCEL et EXPORT_PDF de Statistiques
            # ============================================================
            print("[1] Archivage des actions EXPORT_EXCEL et EXPORT_PDF de la section Statistiques...")
            
            cursor.execute("""
                SELECT ID FROM dbo.WEB_SECTIONS 
                WHERE ID_Proj = ? AND Nom = 'Statistiques'
            """, (id_proj,))
            section_stats = cursor.fetchone()
            
            if section_stats:
                id_section_stats = section_stats.ID
                
                # Archiver EXPORT_EXCEL
                cursor.execute("""
                    UPDATE dbo.WEB_DROITS_ACCES 
                    SET archive = 1 
                    WHERE ID_Section = ? AND Action = 'EXPORT_EXCEL' AND archive = 0
                """, (id_section_stats,))
                if cursor.rowcount > 0:
                    print(f"  ✓ EXPORT_EXCEL archivé (section Statistiques)")
                else:
                    print(f"  (déjà archivé ou absent) EXPORT_EXCEL")
                
                # Archiver EXPORT_PDF
                cursor.execute("""
                    UPDATE dbo.WEB_DROITS_ACCES 
                    SET archive = 1 
                    WHERE ID_Section = ? AND Action = 'EXPORT_PDF' AND archive = 0
                """, (id_section_stats,))
                if cursor.rowcount > 0:
                    print(f"  ✓ EXPORT_PDF archivé (section Statistiques)")
                else:
                    print(f"  (déjà archivé ou absent) EXPORT_PDF")
            else:
                print("  [WARN] Section 'Statistiques' introuvable")
            
            print()

            # ============================================================
            # ÉTAPE 2: Ajouter EXPORT_EXCEL et EXPORT_PDF à Liste des Traitements
            # ============================================================
            print("[2] Ajout des actions EXPORT_EXCEL et EXPORT_PDF à la section Liste des Traitements...")
            
            cursor.execute("""
                SELECT ID FROM dbo.WEB_SECTIONS 
                WHERE ID_Proj = ? AND Nom = 'Liste des Traitements'
            """, (id_proj,))
            section_liste = cursor.fetchone()
            
            if section_liste:
                id_section_liste = section_liste.ID
                
                # Ajouter EXPORT_EXCEL
                cursor.execute("""
                    INSERT INTO dbo.WEB_DROITS_ACCES (ID_Section, Action, archive)
                    SELECT ?, 'EXPORT_EXCEL', 0
                    WHERE NOT EXISTS (
                        SELECT 1 FROM dbo.WEB_DROITS_ACCES 
                        WHERE ID_Section = ? AND Action = 'EXPORT_EXCEL'
                    )
                """, (id_section_liste, id_section_liste))
                if cursor.rowcount > 0:
                    print(f"  + EXPORT_EXCEL ajouté")
                else:
                    print(f"  (déjà présent) EXPORT_EXCEL")
                
                # Ajouter EXPORT_PDF
                cursor.execute("""
                    INSERT INTO dbo.WEB_DROITS_ACCES (ID_Section, Action, archive)
                    SELECT ?, 'EXPORT_PDF', 0
                    WHERE NOT EXISTS (
                        SELECT 1 FROM dbo.WEB_DROITS_ACCES 
                        WHERE ID_Section = ? AND Action = 'EXPORT_PDF'
                    )
                """, (id_section_liste, id_section_liste))
                if cursor.rowcount > 0:
                    print(f"  + EXPORT_PDF ajouté")
                else:
                    print(f"  (déjà présent) EXPORT_PDF")
            else:
                print("  [WARN] Section 'Liste des Traitements' introuvable")
            
            print()

            cursor.connection.commit()

            # Afficher le récapitulatif
            print("=" * 70)
            print("Récapitulatif")
            print("=" * 70)
            
            # Actions actives du Projet 11
            print("\nActions ACTIVES du Projet 11 dans WEB_DROITS_ACCES :")
            cursor.execute("""
                SELECT 
                    s.Nom AS Section,
                    da.Action,
                    da.archive
                FROM dbo.WEB_DROITS_ACCES da
                INNER JOIN dbo.WEB_SECTIONS s ON s.ID = da.ID_Section
                INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
                WHERE p.NumProj = 11 AND da.archive = 0
                ORDER BY s.Nom, da.Action
            """)
            for row in cursor.fetchall():
                print(f"  {row.Section} | {row.Action}")

            print("\nActions ARCHIVÉES du Projet 11 dans WEB_DROITS_ACCES :")
            cursor.execute("""
                SELECT 
                    s.Nom AS Section,
                    da.Action,
                    da.archive
                FROM dbo.WEB_DROITS_ACCES da
                INNER JOIN dbo.WEB_SECTIONS s ON s.ID = da.ID_Section
                INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
                WHERE p.NumProj = 11 AND da.archive = 1
                ORDER BY s.Nom, da.Action
            """)
            archived = cursor.fetchall()
            if archived:
                for row in archived:
                    print(f"  {row.Section} | {row.Action} (archivé)")
            else:
                print("  (aucune)")

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
    modifier_actions_projet11()
