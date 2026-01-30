#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Insertion des actions pour chaque section du Projet 11 dans WEB_DROITS_ACCES.

Sections du Projet 11 :
- Nouvelle fiche de production
- Liste des Traitements
- Statistiques

Actions par section :
1. Nouvelle fiche de production :
   - SAISIE

2. Liste des Traitements :
   - CONSULTATION
   - MODIFICATION
   - SUPPRESSION
   - SAISIE

3. Statistiques :
   - CONSULTATION
   - EXPORT_EXCEL
   - EXPORT_PDF

Utilise la configuration de db.py. Idempotent : pas de doublon si re-exécution.
"""

from db import get_db_cursor

# Définition des actions par section (nom exact tel qu'affiché dans WEB_SECTIONS)
ACTIONS_PAR_SECTION = {
    "Nouvelle fiche de production": [
        "SAISIE",
    ],
    "Liste des Traitements": [
        "CONSULTATION",
        "MODIFICATION",
        "SUPPRESSION",
        "SAISIE",
    ],
    "Statistiques": [
        "CONSULTATION",
        "EXPORT_EXCEL",
        "EXPORT_PDF",
    ],
}


def inserer_actions_projet11():
    """Insère les actions pour chaque section du Projet 11 dans WEB_DROITS_ACCES."""
    print("=" * 70)
    print("Insertion des actions du Projet 11 dans WEB_DROITS_ACCES")
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
                print("  Exécutez d'abord: python creer_table_web_droits_acces.py")
                return False

            # Récupérer l'ID du Projet 11
            cursor.execute("SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = 11")
            proj_row = cursor.fetchone()
            if not proj_row:
                print("[ERREUR] Projet 11 introuvable dans WEB_PROJETS.")
                return False
            id_proj = proj_row.ID

            total_inserted = 0
            total_existing = 0

            # Pour chaque section du Projet 11
            for nom_section, actions in ACTIONS_PAR_SECTION.items():
                # Récupérer l'ID de la section
                cursor.execute("""
                    SELECT ID FROM dbo.WEB_SECTIONS 
                    WHERE ID_Proj = ? AND Nom = ?
                """, (id_proj, nom_section))
                section_row = cursor.fetchone()
                
                if not section_row:
                    print(f"[WARN] Section '{nom_section}' introuvable dans WEB_SECTIONS pour le Projet 11.")
                    print(f"  Actions non insérées pour cette section.")
                    print()
                    continue

                id_section = section_row.ID
                print(f"[{nom_section}] (ID_Section={id_section})")

                # Insérer chaque action
                for action in actions:
                    cursor.execute("""
                        INSERT INTO dbo.WEB_DROITS_ACCES (ID_Section, Action, archive)
                        SELECT ?, ?, 0
                        WHERE NOT EXISTS (
                            SELECT 1 FROM dbo.WEB_DROITS_ACCES 
                            WHERE ID_Section = ? AND Action = ?
                        )
                    """, (id_section, action, id_section, action))

                    if cursor.rowcount > 0:
                        print(f"  + {action}")
                        total_inserted += 1
                    else:
                        print(f"  (déjà présente) {action}")
                        total_existing += 1

                print()

            cursor.connection.commit()

            # Afficher le récapitulatif
            print("=" * 70)
            print("Récapitulatif")
            print("=" * 70)
            print(f"Actions insérées: {total_inserted}")
            print(f"Actions déjà présentes: {total_existing}")
            print()

            # Afficher toutes les actions du Projet 11
            print("Actions du Projet 11 dans WEB_DROITS_ACCES :")
            cursor.execute("""
                SELECT 
                    s.Nom AS Section,
                    da.Action,
                    da.archive
                FROM dbo.WEB_DROITS_ACCES da
                INNER JOIN dbo.WEB_SECTIONS s ON s.ID = da.ID_Section
                INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
                WHERE p.NumProj = 11
                ORDER BY s.Nom, da.Action
            """)
            for row in cursor.fetchall():
                archive_status = "archivé" if row.archive == 1 else "actif"
                print(f"  {row.Section} | {row.Action} ({archive_status})")

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
    inserer_actions_projet11()
