"""
Script pour supprimer la colonne id de la table personel
et restaurer Matricule comme identifiant technique unique (PRIMARY KEY)
"""

from db import get_db_cursor

def supprimer_id_personel():
    """Supprime la colonne id et restaure Matricule comme PRIMARY KEY"""
    
    try:
        with get_db_cursor() as cursor:
            print("[INFO] Debut de la suppression de la colonne id de la table personel...")
            print("")
            
            # Vérifier si la colonne id existe
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'personel' AND COLUMN_NAME = 'id'
            """)
            
            id_exists = cursor.fetchone() is not None
            
            if not id_exists:
                print("[ATTENTION] La colonne id n'existe pas dans la table personel")
                return False
            
            # Vérifier si Matricule existe
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'personel' AND COLUMN_NAME = 'Matricule'
            """)
            
            matricule_exists = cursor.fetchone() is not None
            
            if not matricule_exists:
                print("[ERREUR] La colonne Matricule n'existe pas dans la table personel")
                return False
            
            # ========================================================================
            # ÉTAPE 1 : Identifier et sauvegarder les contraintes de clé étrangère
            # ========================================================================
            print("[ETAPE 1] Identification des contraintes de cle etrangere...")
            cursor.execute("""
                SELECT 
                    fk.name AS fk_name,
                    OBJECT_NAME(fk.parent_object_id) AS parent_table,
                    COL_NAME(fc.parent_object_id, fc.parent_column_id) AS parent_column,
                    COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS referenced_column
                FROM sys.foreign_keys fk
                INNER JOIN sys.foreign_key_columns fc ON fk.object_id = fc.constraint_object_id
                WHERE fk.referenced_object_id = OBJECT_ID('dbo.personel')
            """)
            
            fk_constraints = cursor.fetchall()
            print(f"    {len(fk_constraints)} contrainte(s) de cle etrangere trouvee(s)")
            
            # Sauvegarder les informations des FK
            fk_info = []
            for fk in fk_constraints:
                fk_info.append({
                    'name': fk.fk_name,
                    'parent_table': fk.parent_table,
                    'parent_column': fk.parent_column,
                    'referenced_column': fk.referenced_column
                })
                print(f"    - {fk.fk_name} sur {fk.parent_table} ({fk.parent_column} -> personel.{fk.referenced_column})")
            
            # ========================================================================
            # ÉTAPE 2 : Supprimer les contraintes de clé étrangère
            # ========================================================================
            print("")
            print("[ETAPE 2] Suppression des contraintes de cle etrangere...")
            for fk in fk_info:
                try:
                    cursor.execute(f"ALTER TABLE dbo.[{fk['parent_table']}] DROP CONSTRAINT [{fk['name']}]")
                    print(f"    [OK] Contrainte FK {fk['name']} supprimee de {fk['parent_table']}")
                except Exception as e:
                    print(f"    [ATTENTION] Erreur lors de la suppression de la FK {fk['name']}: {e}")
            
            # ========================================================================
            # ÉTAPE 3 : Supprimer la clé primaire actuelle (sur id)
            # ========================================================================
            print("")
            print("[ETAPE 3] Suppression de la cle primaire actuelle...")
            cursor.execute("""
                SELECT name
                FROM sys.key_constraints
                WHERE type = 'PK' 
                  AND parent_object_id = OBJECT_ID('dbo.personel')
            """)
            
            pk_row = cursor.fetchone()
            if pk_row:
                pk_name = pk_row.name
                try:
                    cursor.execute(f"ALTER TABLE dbo.personel DROP CONSTRAINT [{pk_name}]")
                    print(f"    [OK] Cle primaire {pk_name} supprimee")
                except Exception as e:
                    print(f"    [ERREUR] Impossible de supprimer la cle primaire: {e}")
                    return False
            else:
                print("    [INFO] Aucune cle primaire trouvee")
            
            # ========================================================================
            # ÉTAPE 4 : Supprimer la contrainte UNIQUE sur Matricule si elle existe
            # ========================================================================
            print("")
            print("[ETAPE 4] Verification de la contrainte UNIQUE sur Matricule...")
            cursor.execute("""
                SELECT name
                FROM sys.key_constraints 
                WHERE type = 'UQ' 
                  AND parent_object_id = OBJECT_ID('dbo.personel')
                  AND name LIKE '%Matricule%'
            """)
            
            uq_row = cursor.fetchone()
            if uq_row:
                uq_name = uq_row.name
                try:
                    cursor.execute(f"ALTER TABLE dbo.personel DROP CONSTRAINT [{uq_name}]")
                    print(f"    [OK] Contrainte UNIQUE {uq_name} supprimee")
                except Exception as e:
                    print(f"    [ATTENTION] Erreur lors de la suppression de la contrainte UNIQUE: {e}")
            else:
                print("    [INFO] Aucune contrainte UNIQUE sur Matricule trouvee")
            
            # ========================================================================
            # ÉTAPE 5 : Supprimer la colonne id
            # ========================================================================
            print("")
            print("[ETAPE 5] Suppression de la colonne id...")
            try:
                cursor.execute("ALTER TABLE dbo.personel DROP COLUMN id")
                print("    [OK] Colonne id supprimee")
            except Exception as e:
                print(f"    [ERREUR] Impossible de supprimer la colonne id: {e}")
                return False
            
            # ========================================================================
            # ÉTAPE 6 : Créer la clé primaire sur Matricule
            # ========================================================================
            print("")
            print("[ETAPE 6] Creation de la cle primaire sur Matricule...")
            try:
                cursor.execute("""
                    ALTER TABLE dbo.personel 
                    ADD CONSTRAINT PK_personel PRIMARY KEY (Matricule)
                """)
                print("    [OK] Cle primaire PK_personel creee sur Matricule")
            except Exception as e:
                print(f"    [ERREUR] Impossible de creer la cle primaire sur Matricule: {e}")
                print("    [INFO] Verifiez que toutes les valeurs de Matricule sont uniques et non NULL")
                return False
            
            # ========================================================================
            # ÉTAPE 7 : Recréer les contraintes de clé étrangère
            # ========================================================================
            print("")
            print("[ETAPE 7] Recreation des contraintes de cle etrangere...")
            for fk in fk_info:
                try:
                    cursor.execute(f"""
                        ALTER TABLE dbo.[{fk['parent_table']}]
                        ADD CONSTRAINT [{fk['name']}] 
                        FOREIGN KEY ([{fk['parent_column']}]) 
                        REFERENCES dbo.personel([{fk['referenced_column']}])
                    """)
                    print(f"    [OK] Contrainte FK {fk['name']} recreee sur {fk['parent_table']} ({fk['parent_column']} -> personel.{fk['referenced_column']})")
                except Exception as e:
                    print(f"    [ATTENTION] Impossible de recreer la FK {fk['name']}: {e}")
                    print(f"    [INFO] Vous devrez recreer manuellement cette contrainte")
            
            # Commit des modifications
            conn = cursor.connection
            conn.commit()
            
            # ========================================================================
            # RÉSUMÉ FINAL
            # ========================================================================
            print("")
            print("[OK] Suppression de la colonne id terminee!")
            print("")
            print("[RESUME] Modifications effectuees:")
            print("   - Colonne id supprimee")
            print("   - Cle primaire PK_personel creee sur Matricule")
            print("")
            
            # Afficher la structure actuelle
            print("[STRUCTURE] Structure actuelle de la table personel:")
            cursor.execute("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    CASE 
                        WHEN COLUMNPROPERTY(OBJECT_ID('dbo.personel'), COLUMN_NAME, 'IsIdentity') = 1 
                        THEN 'OUI' 
                        ELSE 'NON' 
                    END AS IS_IDENTITY
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'personel'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns = cursor.fetchall()
            for col in columns:
                identity = " (IDENTITY)" if col.IS_IDENTITY == "OUI" else ""
                nullable = "NULL" if col.IS_NULLABLE == "YES" else "NOT NULL"
                length = f"({col.CHARACTER_MAXIMUM_LENGTH})" if col.CHARACTER_MAXIMUM_LENGTH else ""
                default = f" DEFAULT {col.COLUMN_DEFAULT}" if col.COLUMN_DEFAULT else ""
                
                # Vérifier si c'est la clé primaire
                cursor.execute("""
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_NAME = 'personel'
                      AND CONSTRAINT_NAME IN (
                          SELECT name FROM sys.key_constraints 
                          WHERE type = 'PK' AND parent_object_id = OBJECT_ID('dbo.personel')
                      )
                      AND COLUMN_NAME = ?
                """, (col.COLUMN_NAME,))
                
                pk_col = cursor.fetchone()
                pk_marker = " (PRIMARY KEY)" if pk_col else ""
                
                print(f"   - {col.COLUMN_NAME}: {col.DATA_TYPE}{length} {nullable}{identity}{default}{pk_marker}")
            
            return True
            
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la suppression de la colonne id: {e}")
        import traceback
        traceback.print_exc()
        try:
            conn = cursor.connection
            conn.rollback()
        except:
            pass
        return False

if __name__ == "__main__":
    supprimer_id_personel()
