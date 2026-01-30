#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script Python pour renommer la table WEB_DROITS_ACCES en WEB_ACTIONS
dans la base novaprint_restored.

Ce script exécute le renommage de la table et de toutes ses contraintes.
"""

from db import get_db_cursor

def renommer_table_web_droits_acces():
    """Renomme WEB_DROITS_ACCES en WEB_ACTIONS avec toutes ses contraintes"""
    
    print("=" * 70)
    print("RENOMMAGE DE WEB_DROITS_ACCES EN WEB_ACTIONS")
    print("=" * 70)
    print()
    
    try:
        with get_db_cursor() as cursor:
            # Vérifier que la table existe
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'WEB_DROITS_ACCES'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                print("[ERREUR] La table WEB_DROITS_ACCES n'existe pas.")
                return False
            
            # Vérifier que la nouvelle table n'existe pas déjà
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'WEB_ACTIONS'
            """)
            new_table_exists = cursor.fetchone()[0] > 0
            
            if new_table_exists:
                print("[ERREUR] La table WEB_ACTIONS existe déjà.")
                return False
            
            print("[1/3] Renommage des contraintes...")
            
            # Renommer la clé primaire
            try:
                cursor.execute("EXEC sp_rename 'PK_WEB_DROITS_ACCES', 'PK_WEB_ACTIONS', 'OBJECT'")
                cursor.connection.commit()
                print("  ✓ Clé primaire renommée: PK_WEB_DROITS_ACCES → PK_WEB_ACTIONS")
            except Exception as e:
                print(f"  ⚠ Clé primaire: {e}")
            
            # Renommer la contrainte UNIQUE
            try:
                cursor.execute("EXEC sp_rename 'UQ_WEB_DROITS_ACCES_ID_Section_Action', 'UQ_WEB_ACTIONS_ID_Section_Action', 'OBJECT'")
                cursor.connection.commit()
                print("  ✓ Contrainte UNIQUE renommée")
            except Exception as e:
                print(f"  ⚠ Contrainte UNIQUE: {e}")
            
            # Renommer la clé étrangère
            try:
                cursor.execute("EXEC sp_rename 'FK_WEB_DROITS_ACCES_ID_Section', 'FK_WEB_ACTIONS_ID_Section', 'OBJECT'")
                cursor.connection.commit()
                print("  ✓ Clé étrangère renommée")
            except Exception as e:
                print(f"  ⚠ Clé étrangère: {e}")
            
            print()
            print("[2/3] Renommage de la table...")
            
            # Renommer la table
            cursor.execute("EXEC sp_rename 'dbo.WEB_DROITS_ACCES', 'WEB_ACTIONS'")
            cursor.connection.commit()
            print("  ✓ Table renommée: WEB_DROITS_ACCES → WEB_ACTIONS")
            print()
            
            print("[3/3] Vérification...")
            
            # Vérifier que la nouvelle table existe
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'WEB_ACTIONS'
            """)
            if cursor.fetchone()[0] > 0:
                print("  ✓ Table WEB_ACTIONS créée avec succès")
            else:
                print("  ✗ ERREUR: Table WEB_ACTIONS non trouvée")
                return False
            
            # Compter les lignes
            cursor.execute("SELECT COUNT(*) FROM dbo.WEB_ACTIONS")
            row_count = cursor.fetchone()[0]
            print(f"  ✓ Nombre de lignes dans WEB_ACTIONS: {row_count}")
            
            print()
            print("=" * 70)
            print("RENOMMAGE TERMINÉ AVEC SUCCÈS")
            print("=" * 70)
            print()
            print("IMPORTANT: N'oubliez pas de mettre à jour le code Python")
            print("           qui référence WEB_DROITS_ACCES pour utiliser")
            print("           WEB_ACTIONS à la place.")
            print()
            
            return True
            
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    renommer_table_web_droits_acces()
