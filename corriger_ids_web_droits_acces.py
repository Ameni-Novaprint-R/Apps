#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Correction des enregistrements spécifiques dans WEB_DROITS_ACCES.

ID 6 : EXPORT_EXCEL, ID_Section = 2
ID 7 : EXPORT_PDF, ID_Section = 2
ID 8 : CONSULTATION, ID_Section = 3
"""

from db import get_db_cursor


def corriger_ids_web_droits_acces():
    """Corrige les enregistrements spécifiques dans WEB_DROITS_ACCES."""
    print("=" * 70)
    print("Correction des enregistrements spécifiques dans WEB_DROITS_ACCES")
    print("=" * 70)
    print()

    try:
        with get_db_cursor() as cursor:
            # Vérifier que la table existe
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_DROITS_ACCES'
            """)
            if cursor.fetchone()[0] == 0:
                print("[ERREUR] La table WEB_DROITS_ACCES n'existe pas.")
                return False

            corrections = [
                (6, 2, "EXPORT_EXCEL"),
                (7, 2, "EXPORT_PDF"),
                (8, 3, "CONSULTATION")
            ]

            print("Corrections à effectuer:")
            for id_record, id_section, action in corrections:
                print(f"  ID {id_record}: ID_Section={id_section}, Action={action}")
            print()

            # Vérifier l'état actuel
            print("État actuel:")
            for id_record, id_section, action in corrections:
                cursor.execute("""
                    SELECT ID, ID_Section, Action, archive 
                    FROM dbo.WEB_DROITS_ACCES 
                    WHERE ID = ?
                """, (id_record,))
                row = cursor.fetchone()
                if row:
                    print(f"  ID {id_record}: ID_Section={row.ID_Section}, Action={row.Action}, archive={row.archive}")
                else:
                    print(f"  ID {id_record}: N'existe pas")
            print()

            # Effectuer les corrections
            print("Application des corrections...")
            for id_record, id_section, action in corrections:
                # Vérifier si l'enregistrement existe
                cursor.execute("SELECT ID FROM dbo.WEB_DROITS_ACCES WHERE ID = ?", (id_record,))
                if cursor.fetchone():
                    # Mettre à jour
                    cursor.execute("""
                        UPDATE dbo.WEB_DROITS_ACCES 
                        SET ID_Section = ?, Action = ?, archive = 0
                        WHERE ID = ?
                    """, (id_section, action, id_record))
                    if cursor.rowcount > 0:
                        print(f"  ✓ ID {id_record} corrigé: ID_Section={id_section}, Action={action}")
                    else:
                        print(f"  (déjà correct) ID {id_record}")
                else:
                    # Créer l'enregistrement
                    cursor.execute("""
                        INSERT INTO dbo.WEB_DROITS_ACCES (ID, ID_Section, Action, archive)
                        VALUES (?, ?, ?, 0)
                    """, (id_record, id_section, action))
                    print(f"  + ID {id_record} créé: ID_Section={id_section}, Action={action}")

            print()

            cursor.connection.commit()

            # Vérifier l'état final
            print("État final après correction:")
            for id_record, id_section, action in corrections:
                cursor.execute("""
                    SELECT ID, ID_Section, Action, archive 
                    FROM dbo.WEB_DROITS_ACCES 
                    WHERE ID = ?
                """, (id_record,))
                row = cursor.fetchone()
                if row:
                    status = "✓" if row.ID_Section == id_section and row.Action == action else "✗"
                    print(f"  {status} ID {id_record}: ID_Section={row.ID_Section}, Action={row.Action}, archive={row.archive}")
                else:
                    print(f"  ✗ ID {id_record}: N'existe pas")
            
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
    corriger_ids_web_droits_acces()
