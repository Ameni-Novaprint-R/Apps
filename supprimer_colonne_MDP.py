"""
Script pour supprimer la colonne MDP (majuscule) de la table personel
"""
from db import get_db_cursor

try:
    with get_db_cursor() as cursor:
        print("=" * 80)
        print("SUPPRESSION DE LA COLONNE MDP (MAJUSCULE)")
        print("=" * 80)
        
        # Vérifier que la colonne MDP existe
        cursor.execute("""
            SELECT COUNT(*) as col_exists
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' 
            AND TABLE_NAME = 'personel' 
            AND COLUMN_NAME = 'MDP'
        """)
        result = cursor.fetchone()
        
        if result and result.col_exists > 0:
            print("\nColonne MDP trouvee. Suppression...")
            
            # Vérifier s'il y a des contraintes sur cette colonne
            cursor.execute("""
                SELECT CONSTRAINT_NAME
                FROM INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE
                WHERE TABLE_SCHEMA = 'dbo'
                AND TABLE_NAME = 'personel'
                AND COLUMN_NAME = 'MDP'
            """)
            constraints = cursor.fetchall()
            
            if constraints:
                print(f"  Contraintes trouvees sur MDP: {len(constraints)}")
                for c in constraints:
                    print(f"    - {c.CONSTRAINT_NAME}")
                    # Supprimer les contraintes d'abord
                    try:
                        cursor.execute(f"ALTER TABLE [dbo].[personel] DROP CONSTRAINT [{c.CONSTRAINT_NAME}]")
                        print(f"      [OK] Contrainte {c.CONSTRAINT_NAME} supprimee")
                    except Exception as e:
                        print(f"      [ERREUR] Impossible de supprimer {c.CONSTRAINT_NAME}: {e}")
            
            # Supprimer la colonne
            try:
                cursor.execute("ALTER TABLE [dbo].[personel] DROP COLUMN [MDP]")
                cursor.connection.commit()
                print("\n[OK] Colonne MDP supprimee avec succes!")
            except Exception as e:
                print(f"\n[ERREUR] Impossible de supprimer la colonne MDP: {e}")
                cursor.connection.rollback()
        else:
            print("\n[INFO] La colonne MDP n'existe pas (deja supprimee ou jamais creee)")
        
        # Vérifier que la colonne mdp (minuscule) existe toujours
        cursor.execute("""
            SELECT COUNT(*) as col_exists
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' 
            AND TABLE_NAME = 'personel' 
            AND COLUMN_NAME = 'mdp'
        """)
        result_mdp = cursor.fetchone()
        
        if result_mdp and result_mdp.col_exists > 0:
            print("\n[OK] La colonne 'mdp' (minuscule) existe toujours")
        else:
            print("\n[ATTENTION] La colonne 'mdp' (minuscule) n'existe pas!")
        
        print("\n" + "=" * 80)
        print("OPERATION TERMINEE")
        print("=" * 80)
            
except Exception as e:
    print(f"\n[ERREUR] {e}")
    import traceback
    traceback.print_exc()
