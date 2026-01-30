#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Correction des actions du Projet 11 dans WEB_DROITS_ACCES.

Configuration finale attendue :
1. Section: Nouvelle fiche de production (ID_Section=1)
   - SAISIE

2. Section: Liste des Traitements (ID_Section=2)
   - CONSULTATION
   - MODIFICATION
   - SUPPRESSION
   - SAISIE
   - EXPORT_EXCEL
   - EXPORT_PDF

3. Section: Statistiques (ID_Section=3)
   - CONSULTATION

Utilise la configuration de db.py. Idempotent : pas de doublon si re-exécution.
"""

from db import get_db_cursor


def corriger_actions_projet11():
    """Corrige les actions du Projet 11 dans WEB_DROITS_ACCES selon la configuration attendue."""
    print("=" * 70)
    print("Correction des actions du Projet 11 dans WEB_DROITS_ACCES")
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

            # Configuration attendue
            CONFIG_ATTENDUE = {
                "Nouvelle fiche de production": ["SAISIE"],
                "Liste des Traitements": ["CONSULTATION", "MODIFICATION", "SUPPRESSION", "SAISIE", "EXPORT_EXCEL", "EXPORT_PDF"],
                "Statistiques": ["CONSULTATION"]
            }

            total_ajoutees = 0
            total_archivees = 0
            total_existantes = 0

            # Pour chaque section
            for nom_section, actions_attendues in CONFIG_ATTENDUE.items():
                print(f"[{nom_section}]")
                
                # Récupérer l'ID de la section
                cursor.execute("""
                    SELECT ID FROM dbo.WEB_SECTIONS 
                    WHERE ID_Proj = ? AND Nom = ?
                """, (id_proj, nom_section))
                section_row = cursor.fetchone()
                
                if not section_row:
                    print(f"  [WARN] Section '{nom_section}' introuvable.")
                    print()
                    continue

                id_section = section_row.ID
                
                # Récupérer les actions actuelles de cette section
                cursor.execute("""
                    SELECT Action, archive FROM dbo.WEB_DROITS_ACCES 
                    WHERE ID_Section = ?
                """, (id_section,))
                actions_actuelles = {row.Action: row.archive for row in cursor.fetchall()}
                
                # Archiver les actions qui ne sont pas dans la liste attendue
                for action_actuelle, archive_status in actions_actuelles.items():
                    if action_actuelle not in actions_attendues:
                        if archive_status == 0:  # Si elle est active, l'archiver
                            cursor.execute("""
                                UPDATE dbo.WEB_DROITS_ACCES 
                                SET archive = 1 
                                WHERE ID_Section = ? AND Action = ? AND archive = 0
                            """, (id_section, action_actuelle))
                            if cursor.rowcount > 0:
                                print(f"  ✓ Archivé: {action_actuelle}")
                                total_archivees += 1
                
                # Ajouter/Activer les actions attendues
                for action in actions_attendues:
                    if action in actions_actuelles:
                        # Action existe déjà
                        if actions_actuelles[action] == 1:
                            # Réactiver si elle était archivée
                            cursor.execute("""
                                UPDATE dbo.WEB_DROITS_ACCES 
                                SET archive = 0 
                                WHERE ID_Section = ? AND Action = ? AND archive = 1
                            """, (id_section, action))
                            if cursor.rowcount > 0:
                                print(f"  ✓ Réactivé: {action}")
                                total_ajoutees += 1
                            else:
                                print(f"  (déjà actif) {action}")
                                total_existantes += 1
                        else:
                            print(f"  (déjà actif) {action}")
                            total_existantes += 1
                    else:
                        # Action n'existe pas, l'ajouter
                        cursor.execute("""
                            INSERT INTO dbo.WEB_DROITS_ACCES (ID_Section, Action, archive)
                            VALUES (?, ?, 0)
                        """, (id_section, action))
                        print(f"  + Ajouté: {action}")
                        total_ajoutees += 1
                
                print()

            cursor.connection.commit()

            # Afficher le récapitulatif
            print("=" * 70)
            print("Récapitulatif")
            print("=" * 70)
            print(f"Actions ajoutées/réactivées: {total_ajoutees}")
            print(f"Actions archivées: {total_archivees}")
            print(f"Actions déjà présentes: {total_existantes}")
            print()

            # Afficher l'état final
            print("État final des actions ACTIVES du Projet 11 :")
            cursor.execute("""
                SELECT 
                    s.Nom AS Section,
                    da.Action
                FROM dbo.WEB_DROITS_ACCES da
                INNER JOIN dbo.WEB_SECTIONS s ON s.ID = da.ID_Section
                INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
                WHERE p.NumProj = 11 AND da.archive = 0
                ORDER BY s.Nom, da.Action
            """)
            for row in cursor.fetchall():
                print(f"  {row.Section} | {row.Action}")

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
    corriger_actions_projet11()
